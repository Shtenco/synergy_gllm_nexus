from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind,ProgramNode
from nexus_gllm.unified_v3.cognitive.higher_order import HigherOrderContext,HigherOrderExecutor,HigherOrderStatus
from nexus_gllm.unified_v3.contracts import Entity,OperatorSymbol,TaskOpcode,TaskProgram,WorldFact,WorldHypothesis
from nexus_gllm.unified_v3.temporal import TemporalLedger

def atom(symbol,query=None):
    params=()
    if query:
        op,src,dst=query;params=(('query_operator',op),('query_src',src),('query_dst',dst))
    return ProgramNode(ProgramKind.ATOM,symbol,params=params)
def world(*rows):
    return WorldHypothesis('w',tuple(WorldFact(OperatorSymbol(op,2),(Entity(a),Entity(b)),True) for op,a,b in rows))
def task(op,a,b):return TaskProgram(TaskOpcode.QUERY_RELATION,op,(a,b))

def test_if_executes_body_only_when_condition_proved():
    w=world(('guard','x','y'),('r','a','b'),('r','b','c'));cond=atom('rule:transitive:guard',('guard','x','y'));body=atom('rule:transitive:r')
    node=ProgramNode(ProgramKind.IF,children=(cond,body));out=HigherOrderExecutor().execute(node,HigherOrderContext(w,task('r','a','c')))
    assert out.status is HigherOrderStatus.EXECUTED and out.execution.truth is True and 'IF:true' in out.trace

def test_if_unresolved_does_not_execute_body():
    w=world(('r','a','b'),('r','b','c'));cond=atom('rule:transitive:guard',('guard','x','y'));body=atom('rule:transitive:r')
    out=HigherOrderExecutor().execute(ProgramNode(ProgramKind.IF,children=(cond,body)),HigherOrderContext(w,task('r','a','c')))
    assert out.status is HigherOrderStatus.UNRESOLVED

def test_inhibit_blocks_when_blocker_is_proved():
    w=world(('block','x','y'),('r','a','b'),('r','b','c'));block=atom('rule:transitive:block',('block','x','y'));body=atom('rule:transitive:r')
    out=HigherOrderExecutor().execute(ProgramNode(ProgramKind.INHIBIT,children=(block,body)),HigherOrderContext(w,task('r','a','c')))
    assert out.status is HigherOrderStatus.INHIBITED and out.execution.truth is None

def test_temporal_executes_against_requested_snapshot():
    ledger=TemporalLedger().assert_fact('state','node','old',1).assert_fact('state','node','new',10,supersede=True);base=world()
    child_old=atom('rule:transitive:state',('state','node','old'));old=ProgramNode(ProgramKind.TEMPORAL,children=(child_old,),params=(('time','5'),))
    child_new=atom('rule:transitive:state',('state','node','new'));cur=ProgramNode(ProgramKind.TEMPORAL,children=(child_new,),params=(('mode','current'),))
    ex=HigherOrderExecutor();assert ex.execute(old,HigherOrderContext(base,task('state','node','old'),ledger)).execution.truth is True;assert ex.execute(cur,HigherOrderContext(base,task('state','node','new'),ledger)).execution.truth is True

def test_counterfactual_add_fact_changes_answer_without_mutating_actual_world():
    w=world(('r','a','b'));child=atom('rule:transitive:r');cf=ProgramNode(ProgramKind.COUNTERFACTUAL,children=(child,),params=(('kind','ADD_FACT'),('operator','r'),('src','b'),('dst','c')))
    ex=HigherOrderExecutor();actual=ex.execute(child,HigherOrderContext(w,task('r','a','c')));changed=ex.execute(cf,HigherOrderContext(w,task('r','a','c')))
    assert actual.execution.truth is None and changed.execution.truth is True and w.world_id=='w' and changed.world_id.endswith(':cf')

def test_never_seen_nested_topology_executes_compositionally():
    ledger=TemporalLedger().assert_fact('state','node','ready',3)
    w=world(('r','a','b'),('guard','g','ok'))
    temporal=ProgramNode(ProgramKind.TEMPORAL,children=(atom('rule:transitive:state',('state','node','ready')),),params=(('mode','current'),))
    inhibitor=ProgramNode(ProgramKind.INHIBIT,children=(atom('rule:transitive:block',('block','x','y')),atom('rule:transitive:guard',('guard','g','ok'))))
    cf=ProgramNode(ProgramKind.COUNTERFACTUAL,children=(atom('rule:transitive:r'),),params=(('kind','ADD_FACT'),('operator','r'),('src','b'),('dst','c')))
    node=ProgramNode(ProgramKind.COMPOSE,children=(temporal,inhibitor,cf))
    out=HigherOrderExecutor().execute(node,HigherOrderContext(w,task('r','a','c'),ledger))
    assert out.status is HigherOrderStatus.UNRESOLVED
    # unresolved blocker is intentionally fail-closed; it must not silently open the inhibited branch


def test_explicit_negative_fact_makes_if_condition_false():
    neg=WorldFact(OperatorSymbol('guard',2),(Entity('x'),Entity('y')),False)
    w=WorldHypothesis('w',(neg,WorldFact(OperatorSymbol('r',2),(Entity('a'),Entity('b')),True),WorldFact(OperatorSymbol('r',2),(Entity('b'),Entity('c')),True)))
    cond=atom('rule:transitive:guard',('guard','x','y'));body=atom('rule:transitive:r')
    out=HigherOrderExecutor().execute(ProgramNode(ProgramKind.IF,children=(cond,body)),HigherOrderContext(w,task('r','a','c')))
    assert out.status is HigherOrderStatus.CONDITION_FALSE and out.execution.truth is False

def test_explicit_negative_blocker_opens_inhibit_body():
    neg=WorldFact(OperatorSymbol('block',2),(Entity('x'),Entity('y')),False)
    w=WorldHypothesis('w',(neg,WorldFact(OperatorSymbol('r',2),(Entity('a'),Entity('b')),True),WorldFact(OperatorSymbol('r',2),(Entity('b'),Entity('c')),True)))
    blocker=atom('rule:transitive:block',('block','x','y'));body=atom('rule:transitive:r')
    out=HigherOrderExecutor().execute(ProgramNode(ProgramKind.INHIBIT,children=(blocker,body)),HigherOrderContext(w,task('r','a','c')))
    assert out.status is HigherOrderStatus.EXECUTED and out.execution.truth is True and 'INHIBIT:open' in out.trace
