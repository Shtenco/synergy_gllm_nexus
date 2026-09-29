from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind,ProgramNode
from nexus_gllm.unified_v3.cognitive.program_compiler import CognitiveProgramCompiler,CompileStatus
from nexus_gllm.unified_v3.contracts import Entity,OperatorSymbol,WorldFact,WorldHypothesis,TaskProgram,TaskOpcode
from nexus_gllm.unified_v3.executor import Executor
def atom(s,params=()):return ProgramNode(ProgramKind.ATOM,s,params=params)
def test_transitive_ast_compiles_and_executes_multihop():
    c=CognitiveProgramCompiler().compile(atom('rule:transitive:r'));assert c.status is CompileStatus.COMPILED and c.execution_mode=='rule_program'
    op=OperatorSymbol('r',2);w=WorldHypothesis('w',(WorldFact(op,(Entity('a'),Entity('b'))),WorldFact(op,(Entity('b'),Entity('c')))));out=Executor().execute(w,c.rule_program,TaskProgram(TaskOpcode.QUERY_RELATION,'r',('a','c')));assert out.truth is True and out.derivation.depth==2
def test_composed_ast_aggregates_multiple_clauses():
    p=ProgramNode(ProgramKind.SEQUENCE,children=(atom('rule:symmetric:r'),atom('rule:transitive:r')));c=CognitiveProgramCompiler().compile(p);assert c.status is CompileStatus.COMPILED and len(c.rule_program.clauses)==2
def test_inverse_atom_executes():
    c=CognitiveProgramCompiler().compile(atom('rule:inverse:parent:child'));op=OperatorSymbol('parent',2);w=WorldHypothesis('w',(WorldFact(op,(Entity('a'),Entity('b'))),));out=Executor().execute(w,c.rule_program,TaskProgram(TaskOpcode.QUERY_RELATION,'child',('b','a')));assert out.truth is True
def test_unknown_rule_atom_is_malformed_but_higher_order_is_validated():
    bad=CognitiveProgramCompiler().compile(atom('rule:teleport:r'));assert bad.status is CompileStatus.MALFORMED
    cf=CognitiveProgramCompiler().compile(ProgramNode(ProgramKind.COUNTERFACTUAL,children=(atom('rule:transitive:r'),),params=(('kind','ADD_FACT'),('operator','r'),('src','b'),('dst','c'))));assert cf.status is CompileStatus.COMPILED and cf.execution_mode=='higher_order'
def test_surface_renaming_preserves_rule_shape():
    a=CognitiveProgramCompiler().compile(atom('rule:transitive:alpha')).rule_program;b=CognitiveProgramCompiler().compile(atom('rule:transitive:nonce_991')).rule_program;assert a.shape_fingerprint()==b.shape_fingerprint()==('TRANSITIVE',)
