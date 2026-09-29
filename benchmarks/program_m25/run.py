from nexus_gllm.unified_v3.cognitive.program_synthesis import *
from nexus_gllm.unified_v3.contracts import *
def world(name,edges):
    op=OperatorSymbol(name,2);return WorldHypothesis(name,tuple(WorldFact(op,(Entity(a),Entity(b)),True) for a,b in edges))
def run():
    demos=(
      ProgramEvidenceCase(world('r',( ('a','b'),('b','c') )),TaskProgram(TaskOpcode.QUERY_RELATION,'r',('a','c')),True),
      ProgramEvidenceCase(world('r',( ('x','y'),('y','z') )),TaskProgram(TaskOpcode.QUERY_RELATION,'r',('x','z')),True),
    )
    target=world('r',( ('p','q'),('q','s') ));task=TaskProgram(TaskOpcode.QUERY_RELATION,'r',('p','s'))
    r=ProgramSynthesisCortex().synthesize(target,task,demos)
    return {'selected':r.selected.canonical() if r.selected else None,'top_score':r.candidates[0].total_score if r.candidates else None,'candidate_count':len(r.candidates)}
