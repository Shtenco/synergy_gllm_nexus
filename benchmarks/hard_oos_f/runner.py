from __future__ import annotations
from dataclasses import dataclass
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind,ProgramNode
from nexus_gllm.unified_v3.cognitive.higher_order import HigherOrderContext,HigherOrderExecutor
from nexus_gllm.unified_v3.contracts import Entity,OperatorSymbol,TaskOpcode,TaskProgram,WorldFact,WorldHypothesis
from nexus_gllm.unified_v3.temporal import TemporalLedger

@dataclass(frozen=True)
class Prediction:case_id:str;status:str;truth:bool|None

def _ast(d):
    return ProgramNode(ProgramKind(d['kind']),d.get('symbol',''),tuple(_ast(c) for c in d.get('children',())),tuple(tuple(x) for x in d.get('params',())))
def _ctx(c):
    world=WorldHypothesis('hard-f',tuple(WorldFact(OperatorSymbol(op,2),(Entity(a),Entity(b)),True) for op,a,b in c.world));op,a,b=c.task;task=TaskProgram(TaskOpcode.QUERY_RELATION,op,(a,b));ledger=TemporalLedger()
    for rel,sub,val,t,sup in c.ledger:ledger=ledger.assert_fact(rel,sub,val,t,supersede=sup)
    return HigherOrderContext(world,task,ledger)

def crc_predict(c):
    out=HigherOrderExecutor().execute(_ast(c.ast),_ctx(c));return Prediction(c.case_id,out.status.value,out.execution.truth)

def fixed_basis_predict(c):
    # Honest historical baseline: higher-order topology is unrepresentable.
    return Prediction(c.case_id,'REPRESENTATION_FAILURE',None)
