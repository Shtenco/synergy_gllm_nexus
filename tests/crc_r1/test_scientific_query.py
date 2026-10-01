from nexus_gllm.unified_v3.cognitive.information_gain import *
from nexus_gllm.unified_v3.cognitive.scientific_query import *
from nexus_gllm.unified_v3.cognitive.action_boundary import *
def prior():return (HypothesisMass('h1',.5),HypothesisMass('h2',.5))
def diagnostic(qid='q',cost=.1,risk=.0):
    return InformationQuery(qid,(QueryOutcome('y',.5,(HypothesisMass('h1',.95),HypothesisMass('h2',.05))),QueryOutcome('n',.5,(HypothesisMass('h1',.05),HypothesisMass('h2',.95)))),cost,risk)
def test_read_only_query_becomes_read_only_action_proposal():
    s=QueryActionSpec(diagnostic(),'web.search','knowledge','web.read',False)
    p=ScientificQueryPlanner().plan(prior(),(s,))
    assert p.action_proposal.risk is ActionRisk.READ_ONLY and p.action_proposal.requested_scope=='web.read'
def test_intervention_is_never_auto_executed_and_gets_medium_risk():
    s=QueryActionSpec(diagnostic(),'lab.intervene','system-x','lab.write',True)
    p=ScientificQueryPlanner().plan(prior(),(s,))
    assert p.action_proposal.risk is ActionRisk.MEDIUM
    assert not ActionBoundary().authorize(p.action_proposal,None).authorized
def test_high_risk_cost_can_make_safer_observation_win():
    a=QueryActionSpec(diagnostic('observe',.05,.0),'sensor.read','x','sensor.read',False)
    b=QueryActionSpec(diagnostic('intervene',.05,1.0),'lab.intervene','x','lab.write',True)
    p=ScientificQueryPlanner(ActiveInformationSelector(risk_weight=1.0)).plan(prior(),(a,b))
    assert p.selected_query_id=='observe'
