from dataclasses import replace
from .contracts import PredictionOutcome
class PredictionLedger:
    def resolve(self,predictions,observations):
        obs={(o[0],o[1],o[2]):o[3] for o in observations}
        out=[]
        for p in predictions:
            key=tuple(p.atom)
            if key not in obs: out.append(replace(p,outcome=PredictionOutcome.UNOBSERVED,score_delta=0.0))
            elif obs[key]==p.expected_polarity: out.append(replace(p,outcome=PredictionOutcome.CONFIRMED,score_delta=1.0))
            else: out.append(replace(p,outcome=PredictionOutcome.REFUTED,score_delta=-1.5))
        return tuple(out)
