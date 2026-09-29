from nexus_gllm.unified_v3.cognitive.promotion import *
def matrix():
    gate=GuardedPromotionGate();cases={
      'clean':PromotionCandidate('clean','a'*64,ReplayMetrics(.9,.05,0),ReplayMetrics(.91,.05,0),True,True),
      'forgetting':PromotionCandidate('forget','b'*64,ReplayMetrics(.9,.05,0),ReplayMetrics(.93,.04,2),True,True),
      'uncalibrated':PromotionCandidate('uncal','c'*64,ReplayMetrics(.9,.05,0),ReplayMetrics(.95,.09,0),True,True),
      'unreplayed':PromotionCandidate('unrep','d'*64,ReplayMetrics(.9,.05,0),ReplayMetrics(.95,.04,0),False,True)}
    return {k:gate.decide(v).__dict__ for k,v in cases.items()}
