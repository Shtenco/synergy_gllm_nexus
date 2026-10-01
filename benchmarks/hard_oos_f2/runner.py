from __future__ import annotations
from dataclasses import dataclass
from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind,ProgramNode
from nexus_gllm.unified_v3.cognitive.higher_order import HigherOrderContext,HigherOrderExecutor
from nexus_gllm.unified_v3.contracts import Entity,OperatorSymbol,TaskOpcode,TaskProgram,WorldFact,WorldHypothesis

@dataclass(frozen=True)
class Prediction: case_id:str;status:str;truth:bool|None

def ast(d): return ProgramNode(ProgramKind(d['kind']),d.get('symbol',''),tuple(ast(c) for c in d.get('children',())),tuple(tuple(x) for x in d.get('params',())))

def ctx(c):
    world=WorldHypothesis('hard-f2',tuple(WorldFact(OperatorSymbol(op,2),(Entity(a),Entity(b)),pol) for op,a,b,pol in c.world))
    op,a,b=c.task;task=TaskProgram(TaskOpcode.QUERY_RELATION,op,(a,b));return HigherOrderContext(world,task)

def crc_predict(c):
    o=HigherOrderExecutor().execute(ast(c.ast),ctx(c));return Prediction(c.case_id,o.status.value,o.execution.truth)

def fixed_basis_predict(c): return Prediction(c.case_id,'REPRESENTATION_FAILURE',None)
