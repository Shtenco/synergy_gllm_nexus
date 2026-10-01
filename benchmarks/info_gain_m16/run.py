from nexus_gllm.unified_v3.cognitive.information_gain import *
def suite():
    prior=(HypothesisMass('H1',.5),HypothesisMass('H2',.5))
    diagnostic=InformationQuery('diagnostic',(
      QueryOutcome('yes',.5,(HypothesisMass('H1',.95),HypothesisMass('H2',.05))),
      QueryOutcome('no',.5,(HypothesisMass('H1',.05),HypothesisMass('H2',.95))),
    ),cost=.1,risk=.05)
    cheap_noise=InformationQuery('cheap_noise',(
      QueryOutcome('yes',.5,(HypothesisMass('H1',.55),HypothesisMass('H2',.45))),
      QueryOutcome('no',.5,(HypothesisMass('H1',.45),HypothesisMass('H2',.55))),
    ),cost=.01,risk=0)
    risky=InformationQuery('risky_perfect',(
      QueryOutcome('yes',.5,(HypothesisMass('H1',1),HypothesisMass('H2',0))),
      QueryOutcome('no',.5,(HypothesisMass('H1',0),HypothesisMass('H2',1))),
    ),cost=.1,risk=1.0)
    return prior,(diagnostic,cheap_noise,risky)
def run():
    prior,qs=suite();best,scores=ActiveInformationSelector(cost_weight=.25,risk_weight=.75).choose(prior,qs)
    return {'selected':best.query_id if best else None,'scores':{s.query_id:s.__dict__ for s in scores}}
