from nexus_gllm.unified_v3.cognitive.replay_bank import *
from nexus_gllm.unified_v3.cognitive.replay_promotion import promotion_candidate_from_replay
from nexus_gllm.unified_v3.cognitive.promotion import GuardedPromotionGate
def bank():
    return FrozenReplayBank((
      ReplayCase('a','formal','1'*64,True,.9),
      ReplayCase('b','memory','2'*64,True,.8),
      ReplayCase('c','causal','3'*64,False,.4),
    ))
def test_replay_manifest_is_deterministic():
    b=bank();m=b.manifest();assert b.verify(m) and len(m['sha256'])==64
def test_regression_and_correction_are_counted_separately():
    r=AntiForgettingEvaluator().evaluate(bank(),(ReplayOutcome('a',False,.8),ReplayOutcome('b',True,.8),ReplayOutcome('c',True,.7)))
    assert r.regression_count==1 and r.correction_count==1
def test_missing_replay_case_fails_closed():
    try:AntiForgettingEvaluator().evaluate(bank(),(ReplayOutcome('a',True,.9),))
    except ValueError:return
    assert False
def test_replay_report_drives_promotion_gate():
    r=AntiForgettingEvaluator().evaluate(bank(),(ReplayOutcome('a',True,.9),ReplayOutcome('b',False,.7),ReplayOutcome('c',True,.6)))
    c=promotion_candidate_from_replay('cand','a'*64,r)
    d=GuardedPromotionGate().decide(c);assert not d.promoted and 'anti_forgetting_regressions' in d.reasons
