from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nexus_gllm.unified_v3.contracts import TaskProgram, WorldHypothesis
from nexus_gllm.unified_v3.temporal import TemporalLedger

from .credit import CognitiveTraceGraph
from .future_tree import BranchValue
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
    """Single typed CRC deliberation/observation loop.

    Deliberation is read-only with respect to authority-owned world facts.
    Learning happens only after explicit observation/reward.
    """
    def __init__(self,core=None,world_model=None):
        self.core=core or CognitiveRecursiveCoreR1()
        self.world_model=world_model
        self.executor=HigherOrderExecutor()

    def deliberate(self,req:CognitiveRequest)->CognitiveDecision:
        state=NexusCognitiveState(req.episode_id,world_id=req.world.world_id,novelty=req.novelty,uncertainty=req.uncertainty)
        meta=self.core.meta.decide(novelty=req.novelty,uncertainty=req.uncertainty,budget=state.budget,self_model=self.core.self_model)
        state=state.transition('meta_control',data={'depth':meta.branch_depth,'fanout':meta.branch_fanout,'experts':meta.expert_top_k,'memory_limit':meta.memory_limit,'abstain':meta.abstain})

        memories=self.core.memory.retrieve(req.memory_tags,limit=meta.memory_limit) if req.memory_tags else ()
        if memories:
            state=state.transition('memory_retrieve',data={'count':len(memories)},memory_ids=tuple(m.memory_id for m in memories))

        execution=self.executor.execute(req.program,HigherOrderContext(req.world,req.task,req.temporal_ledger))
        state=state.transition('program_execute',ref_id=req.program.program_id,data={'status':execution.status.value,'truth':execution.execution.truth},program_ids=(req.program.program_id,))

        plan=None
        if self.world_model is not None and req.planning_state is not None and not meta.abstain:
            plan=LearnedFuturePlanner(self.world_model,max_depth=meta.branch_depth,fanout=meta.branch_fanout).plan(req.planning_state)
            state=state.transition('future_plan',ref_id=plan.branch_id,data={'action':plan.action,'value':plan.value,'depth':plan.depth},branch_id=plan.branch_id,predicted_reward=plan.value)

        graph=CognitiveTraceGraph()
        graph.add_node('meta','meta',{'capability':'meta_control'})
        last='meta'
        for i,m in enumerate(memories):
            nid=f'memory:{i}:{m.memory_id}'
            graph.add_node(nid,'memory',{'capability':'memory_retrieval','memory_id':m.memory_id})
            graph.connect(last,nid,1.0);last=nid
        graph.add_node('program:'+req.program.program_id,'program',{'capability':'program_execution'})
        graph.connect(last,'program:'+req.program.program_id,1.0);last='program:'+req.program.program_id
        if plan is not None:
            graph.add_node('branch:'+str(plan.branch_id),'branch',{'capability':'future_planning','action':plan.action})
            graph.connect(last,'branch:'+str(plan.branch_id),1.0);last='branch:'+str(plan.branch_id
            )
        graph.add_node('answer','answer',{'capability':'answer_selection'})
        graph.connect(last,'answer',1.0)

        answer=execution.execution.truth
        return CognitiveDecision(state,meta,tuple(memories),execution,plan,graph,answer)

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
