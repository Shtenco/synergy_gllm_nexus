from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nexus_gllm.unified_v3.contracts import TaskProgram, WorldHypothesis
from nexus_gllm.unified_v3.temporal import TemporalLedger

from .credit import CognitiveTraceGraph
from .higher_order import HigherOrderContext,HigherOrderExecutor,HigherOrderResult
from .learned_planner import LearnedFuturePlanner,PlannedAction
from .memory import MemoryRecord
from .meta_controller import MetaDecision
from .program_ast import ProgramNode
from .reward import RewardVector
from .runtime import CognitiveRecursiveCoreR1,CognitiveOutcome
from .state import NexusCognitiveState


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


@dataclass(frozen=True)
class CognitiveDecision:
    state:NexusCognitiveState
    meta:MetaDecision
    memories:tuple[MemoryRecord,...]
    execution:HigherOrderResult
    plan:PlannedAction|None
    trace_graph:CognitiveTraceGraph
    answer:Any


class CognitiveLoopR1:
    """Single typed CRC deliberation/observation loop."""
    def __init__(self,core=None,world_model=None):
        self.core=core or CognitiveRecursiveCoreR1()
        self.world_model=world_model
        self.executor=HigherOrderExecutor()

    def deliberate(self,req:CognitiveRequest)->CognitiveDecision:
        state=NexusCognitiveState(
            req.episode_id,
            world_id=req.world.world_id,
            novelty=req.novelty,
            uncertainty=req.uncertainty,
            predicted_reward=float(req.predicted_outcome_reward),
        )
        meta=self.core.meta.decide(
            novelty=req.novelty,
            uncertainty=req.uncertainty,
            budget=state.budget,
            self_model=self.core.self_model,
        )
        state=state.transition(
            'meta_control',
            data={
                'depth':meta.branch_depth,
                'fanout':meta.branch_fanout,
                'experts':meta.expert_top_k,
                'memory_limit':meta.memory_limit,
                'abstain':meta.abstain,
            },
        )

        memories=self.core.memory.retrieve(req.memory_tags,limit=meta.memory_limit) if req.memory_tags else ()
        if memories:
            state=state.transition(
                'memory_retrieve',
                data={'count':len(memories)},
                memory_ids=tuple(m.memory_id for m in memories),
            )

        execution=self.executor.execute(
            req.program,
            HigherOrderContext(req.world,req.task,req.temporal_ledger),
        )
        state=state.transition(
            'program_execute',
            ref_id=req.program.program_id,
            data={'status':execution.status.value,'truth':execution.execution.truth},
            program_ids=(req.program.program_id,),
        )

        plan=None
        if self.world_model is not None and req.planning_state is not None and not meta.abstain:
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

        graph=CognitiveTraceGraph()
        graph.add_node('meta','meta',{'capability':'meta_control'})

        program_id='program:'+req.program.program_id
        graph.add_node(program_id,'program',{'capability':'program_execution'})

        # Memories are parallel evidence/retrieval contributors to the program,
        # never an arbitrary ordered causal chain.
        if memories:
            for i,m in enumerate(memories):
                nid=f'memory:{i}:{m.memory_id}'
                graph.add_node(nid,'memory',{'capability':'memory_retrieval','memory_id':m.memory_id})
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

        graph.add_node('answer','answer',{'capability':'answer_selection'})
        graph.connect(last,'answer',1.0)

        return CognitiveDecision(
            state,
            meta,
            tuple(memories),
            execution,
            plan,
            graph,
            execution.execution.truth,
        )

    def observe(self,decision:CognitiveDecision,reward:RewardVector,*,counterfactual_credit=None)->CognitiveOutcome:
        graph=decision.trace_graph
        if 'outcome' not in graph.nodes:
            graph.add_node('outcome','outcome',{'capability':'outcome'})
            graph.connect('answer','outcome',1.0)
        return self.core.close_episode(
            decision.state,
            answer=decision.answer,
            reward=reward,
            trace_graph=graph,
            outcome_node_id='outcome',
            counterfactual_credit=counterfactual_credit,
        )
