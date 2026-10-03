from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from nexus_gllm.unified_v3.contracts import TaskProgram, WorldFact, WorldHypothesis
from nexus_gllm.unified_v3.temporal import TemporalLedger

from .ablation import CognitiveLoopConfig, ComputeLedger
from .causal_model import CausalEdge,CausalEvidence,CausalGraph
from .credit import CognitiveTraceGraph
from .higher_order import HigherOrderContext,HigherOrderExecutor,HigherOrderResult
from .learned_planner import LearnedFuturePlanner,PlannedAction
from .memory import MemoryLevel,MemoryRecord
from .meta_controller import MetaDecision
from .program_ast import ProgramNode
from .reward import RewardVector
from .runtime import CognitiveRecursiveCoreR1,CognitiveOutcome
from .state import ComputeBudget,NexusCognitiveState


@dataclass(frozen=True)
class CognitiveRequest:
    episode_id:str
    world:WorldHypothesis
    task:TaskProgram
    program:ProgramNode
    novelty:float=0.0
    uncertainty:float=1.0
    memory_tags:tuple[str,...]=()
    temporal_ledger:TemporalLedger|None=None
    planning_state:str|None=None
    predicted_outcome_reward:float=0.0
    capability_hints:tuple[str,...]=()
    causal_query:tuple[str,str]|None=None
    causal_evidence:tuple[CausalEvidence,...]=()


@dataclass(frozen=True)
class CognitiveDecision:
    state:NexusCognitiveState
    meta:MetaDecision
    memories:tuple[MemoryRecord,...]
    execution:HigherOrderResult
    plan:PlannedAction|None
    causal_edge:CausalEdge|None
    compute:ComputeLedger
    trace_graph:CognitiveTraceGraph
    answer:Any


class CognitiveLoopR1:
    """Single typed CRC deliberation/observation loop.

    A cumulative ablation config can disable organs without changing the shared
    execution path or the frozen normalized compute-price schedule. ``config``
    defaults to the full pre-ablation CRC behavior.
    """
    def __init__(self,core=None,world_model=None,*,config:CognitiveLoopConfig|None=None):
        self.core=core or CognitiveRecursiveCoreR1()
        self.world_model=world_model
        self.executor=HigherOrderExecutor()
        self.config=config or CognitiveLoopConfig.full()

    @staticmethod
    def _program_nodes_by_path(root:ProgramNode)->dict[tuple[int,...],ProgramNode]:
        out={}
        def walk(node:ProgramNode,path:tuple[int,...]):
            out[path]=node
            for index,child in enumerate(node.children):
                walk(child,path+(index,))
        walk(root,())
        return out

    @staticmethod
    def _add_program_dag(graph:CognitiveTraceGraph,root:ProgramNode,execution:HigherOrderResult)->str:
        nodes_by_path=CognitiveLoopR1._program_nodes_by_path(root)
        graph_id_by_path={}
        for step in execution.steps:
            node=nodes_by_path.get(step.step_path)
            if node is None:
                raise ValueError(f'executed proof step has no AST occurrence: {step.step_path}')
            identity=execution.step_identity(step)
            graph_id='program:'+identity
            graph_id_by_path[step.step_path]=graph_id
            graph.add_node(
                graph_id,
                'program',
                {
                    'capability':'program_execution',
                    'program_id':step.program_id,
                    'step_path':step.step_path,
                    'ast_kind':step.ast_kind.value,
                    'symbol':node.symbol,
                    'status':step.status.value,
                    'truth':step.execution.truth,
                    'world_id':step.world_id,
                    'evidence_kind':step.evidence_kind,
                    'verified':step.verified,
                },
            )
        for path,child_id in graph_id_by_path.items():
            if not path:
                continue
            parent_id=graph_id_by_path.get(path[:-1])
            if parent_id is not None:
                graph.connect(child_id,parent_id,1.0)
        root_id=graph_id_by_path.get(())
        if root_id is None:
            raise ValueError('execution ledger has no root proof occurrence')
        return root_id

    @staticmethod
    def _causal_edge(req:CognitiveRequest)->CausalEdge|None:
        if req.causal_query is None:
            return None
        cause,effect=req.causal_query
        model=CausalGraph()
        for evidence in req.causal_evidence:
            model.add(evidence)
        return model.edge(cause,effect)

    @staticmethod
    def _ground_memory_world(base:WorldHypothesis,memories:tuple[MemoryRecord,...])->tuple[WorldHypothesis,tuple[str,...]]:
        """Admit only provenance-backed semantic WorldFact memories as world evidence."""
        accepted=[]
        facts=list(base.facts)
        for memory in memories:
            if memory.level is not MemoryLevel.SEMANTIC:
                continue
            if memory.confidence < 0.9 or not memory.raw_provenance:
                continue
            if not isinstance(memory.payload,WorldFact):
                continue
            if memory.payload in facts:
                continue
            facts.append(memory.payload)
            accepted.append(memory.memory_id)
        if not accepted:
            return base,()
        grounded=WorldHypothesis(
            base.world_id+':memory',
            tuple(facts),
            parent_world_id=base.world_id,
        )
        return grounded,tuple(accepted)

    @staticmethod
    def _fixed_meta(budget:ComputeBudget)->MetaDecision:
        return MetaDecision(
            branch_depth=budget.max_depth,
            branch_fanout=budget.max_fanout,
            expert_top_k=budget.max_experts,
            memory_limit=budget.max_memory_records,
            abstain=False,
            reason='fixed_ablation_policy',
            verification_level=3,
            weak_capabilities=(),
        )

    def _spend(self,ledger:ComputeLedger,module:str)->ComputeLedger:
        return ledger.spend(module,self.config.costs.for_module(module))

    def deliberate(self,req:CognitiveRequest)->CognitiveDecision:
        state=NexusCognitiveState(
            req.episode_id,
            world_id=req.world.world_id,
            novelty=req.novelty,
            uncertainty=req.uncertainty,
            predicted_reward=float(req.predicted_outcome_reward),
            budget=ComputeBudget(remaining_units=self.config.budget_units),
        )
        compute=ComputeLedger(self.config.budget_units)

        if self.config.enable_meta:
            compute=self._spend(compute,'meta')
            meta=self.core.meta.decide(
                novelty=req.novelty,
                uncertainty=req.uncertainty,
                budget=state.budget,
                self_model=self.core.self_model,
                capability_hints=req.capability_hints,
                calibration_ledger=self.core.calibration,
            )
        else:
            meta=self._fixed_meta(state.budget)
        state=state.transition(
            'meta_control',
            data={
                'adaptive':self.config.enable_meta,
                'depth':meta.branch_depth,
                'fanout':meta.branch_fanout,
                'experts':meta.expert_top_k,
                'memory_limit':meta.memory_limit,
                'abstain':meta.abstain,
                'verification_level':meta.verification_level,
                'weak_capabilities':meta.weak_capabilities,
            },
        )

        memories=()
        if self.config.enable_memory and req.memory_tags:
            compute=self._spend(compute,'memory')
            memories=self.core.memory.retrieve(req.memory_tags,limit=meta.memory_limit)
        if memories:
            state=state.transition(
                'memory_retrieve',
                data={'count':len(memories)},
                memory_ids=tuple(m.memory_id for m in memories),
            )

        reasoning_world,accepted_memory_ids=self._ground_memory_world(req.world,tuple(memories))
        if accepted_memory_ids:
            state=state.transition(
                'memory_grounding',
                data={
                    'accepted_fact_count':len(accepted_memory_ids),
                    'accepted_memory_ids':accepted_memory_ids,
                },
                world_id=reasoning_world.world_id,
            )

        compute=self._spend(compute,'program')
        execution=self.executor.execute(
            req.program,
            HigherOrderContext(reasoning_world,req.task,req.temporal_ledger),
        )
        coverage=execution.proof_coverage
        state_steps=tuple(sorted(execution.steps,key=lambda step:(len(step.step_path),step.step_path)))
        state=state.transition(
            'program_execute',
            ref_id=req.program.program_id,
            data={
                'status':execution.status.value,
                'truth':execution.execution.truth,
                'program_node_count':len(execution.steps),
                'verified_program_node_count':len(coverage.verified_node_ids),
                'program_step_ids':tuple(execution.step_identity(step) for step in state_steps),
                'proof_coverage':coverage.coverage,
                'proof_complete':coverage.complete,
            },
            program_ids=tuple(step.program_id for step in state_steps),
        )

        causal_edge=None
        if self.config.enable_causal and req.causal_query is not None:
            compute=self._spend(compute,'causal')
            causal_edge=self._causal_edge(req)
        if causal_edge is not None:
            cause,effect=req.causal_query
            state=state.transition(
                'causal_inference',
                ref_id=f'{cause}->{effect}',
                data={
                    'identified':causal_edge.identified,
                    'confidence':causal_edge.confidence,
                    'observational_mass':causal_edge.observational_mass,
                    'interventional_mass':causal_edge.interventional_mass,
                    'counterfactual_mass':causal_edge.counterfactual_mass,
                    'contradiction_mass':causal_edge.contradiction_mass,
                },
            )

        plan=None
        if self.config.enable_future and self.world_model is not None and req.planning_state is not None and not meta.abstain:
            compute=self._spend(compute,'future')
            plan=LearnedFuturePlanner(
                self.world_model,
                max_depth=meta.branch_depth,
                fanout=meta.branch_fanout,
            ).plan(req.planning_state)
            state=state.transition(
                'future_plan',
                ref_id=plan.branch_id,
                data={'action':plan.action,'planning_value':plan.value,'depth':plan.depth},
                branch_id=plan.branch_id,
            )

        state=replace(state,budget=state.budget.spend(compute.spent_units))

        graph=CognitiveTraceGraph()
        graph.add_node('meta','meta',{'capability':'meta_control','adaptive':self.config.enable_meta})
        program_id=self._add_program_dag(graph,req.program,execution)

        if memories:
            accepted=set(accepted_memory_ids)
            for i,m in enumerate(memories):
                nid=f'memory:{i}:{m.memory_id}'
                graph.add_node(
                    nid,
                    'memory',
                    {
                        'capability':'memory_retrieval',
                        'memory_id':m.memory_id,
                        'grounded':m.memory_id in accepted,
                    },
                )
                graph.connect('meta',nid,1.0)
                graph.connect(nid,program_id,1.0)
        else:
            graph.connect('meta',program_id,1.0)

        last=program_id
        if plan is not None:
            branch_id='branch:'+str(plan.branch_id)
            graph.add_node(branch_id,'branch',{'capability':'future_planning','action':plan.action,'planning_value':plan.value})
            graph.connect(program_id,branch_id,1.0)
            last=branch_id

        causal_id=None
        if causal_edge is not None:
            cause,effect=req.causal_query
            causal_id=f'causal:{cause}->{effect}'
            graph.add_node(
                causal_id,
                'causal',
                {
                    'capability':'causal_inference',
                    'cause':cause,
                    'effect':effect,
                    'identified':causal_edge.identified,
                    'confidence':causal_edge.confidence,
                    'observational_mass':causal_edge.observational_mass,
                    'interventional_mass':causal_edge.interventional_mass,
                    'counterfactual_mass':causal_edge.counterfactual_mass,
                    'contradiction_mass':causal_edge.contradiction_mass,
                },
            )
            graph.connect('meta',causal_id,1.0)

        causal_gate_required=self.config.enable_causal and req.causal_query is not None
        causal_gate_open=(causal_edge.identified if causal_edge is not None else not causal_gate_required)
        answer=execution.execution.truth if causal_gate_open else None

        graph.add_node(
            'answer',
            'answer',
            {
                'capability':'answer_selection',
                'proof_complete':coverage.complete,
                'proof_coverage':coverage.coverage,
                'unverified_program_ids':coverage.unverified_node_ids,
                'causal_gate_required':causal_gate_required,
                'causal_gate_open':causal_gate_open,
                'compute_spent':compute.spent_units,
                'compute_budget':compute.budget_units,
            },
        )
        graph.connect(last,'answer',1.0)
        if causal_id is not None:
            graph.connect(causal_id,'answer',1.0)

        return CognitiveDecision(
            state,
            meta,
            tuple(memories),
            execution,
            plan,
            causal_edge,
            compute,
            graph,
            answer,
        )

    def observe(self,decision:CognitiveDecision,reward:RewardVector,*,counterfactual_credit=None)->CognitiveOutcome:
        graph=decision.trace_graph
        if 'outcome' not in graph.nodes:
            graph.add_node('outcome','outcome',{'capability':'outcome'})
            graph.connect('answer','outcome',1.0)

        if not self.config.enable_credit:
            observed=self.core.rpe.observed(reward)
            final=decision.state.transition(
                'outcome',
                ref_id='outcome',
                data={'rpe':0.0,'credit_disabled':True},
                observed_reward=observed,
            )
            return CognitiveOutcome(final,decision.answer,observed,0.0,{})

        # D/E reserve the frozen credit cost from the same episode budget.
        self._spend(decision.compute,'credit')
        return self.core.close_episode(
            decision.state,
            answer=decision.answer,
            reward=reward,
            trace_graph=graph,
            outcome_node_id='outcome',
            counterfactual_credit=counterfactual_credit,
        )