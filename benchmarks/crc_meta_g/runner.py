from __future__ import annotations
from dataclasses import dataclass
from nexus_gllm.unified_v3.cognitive.cognitive_loop import CognitiveLoopR1,CognitiveRequest
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind,ProgramNode
from nexus_gllm.unified_v3.cognitive.reward import RewardVector
from nexus_gllm.unified_v3.cognitive.world_model import EmpiricalWorldModel
from nexus_gllm.unified_v3.contracts import Entity,OperatorSymbol,TaskOpcode,TaskProgram,WorldFact,WorldHypothesis
from nexus_gllm.unified_v3.temporal import TemporalLedger

@dataclass(frozen=True)
class Prediction:
    case_id:str
    execution_status:str
    execution_truth:bool|None
    first_action:str|None
    memory_count:int
    trace_kinds:tuple[str,...]

def _ast(d):
    return ProgramNode(ProgramKind(d['kind']),d.get('symbol',''),tuple(_ast(c) for c in d.get('children',())),tuple(tuple(x) for x in d.get('params',())))

def _build(case):
    wm=EmpiricalWorldModel()
    for s,a,n,r in case.transitions:
        for _ in range(3):wm.observe(s,a,n,r)
    loop=CognitiveLoopR1(world_model=wm)
    for payload,evidence in case.memory:
        loop.core.memory.add_raw({'payload':payload,'evidence':evidence},tags=case.memory_tags)
    world=WorldHypothesis('meta-g:'+case.case_id,tuple(WorldFact(OperatorSymbol(op,2),(Entity(a),Entity(b)),True) for op,a,b in case.world))
    op,a,b=case.task;task=TaskProgram(TaskOpcode.QUERY_RELATION,op,(a,b))
    ledger=TemporalLedger()
    for rel,sub,val,t,sup in case.ledger:ledger=ledger.assert_fact(rel,sub,val,t,supersede=sup)
    req=CognitiveRequest(case.case_id,world,task,_ast(case.ast),case.novelty,case.uncertainty,case.memory_tags,ledger,case.planning_state,case.predicted_outcome_reward)
    return loop,req

def decide(case):
    loop,req=_build(case);d=loop.deliberate(req)
    return loop,d,Prediction(case.case_id,d.execution.status.value,d.execution.execution.truth,d.plan.action if d.plan else None,len(d.memories),tuple(n.kind for n in d.trace_graph.nodes.values()))

def observe(loop,decision,gold):
    return loop.observe(decision,RewardVector(task=gold.observed_task_reward))
