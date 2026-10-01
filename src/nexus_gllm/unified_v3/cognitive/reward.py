from dataclasses import dataclass
@dataclass(frozen=True)
class RewardVector:
    task:float=0.0;information_gain:float=0.0;causal_consistency:float=0.0;progress:float=0.0;calibration_gain:float=0.0;contradiction:float=0.0;compute_cost:float=0.0;risk:float=0.0
@dataclass(frozen=True)
class RewardWeights:
    task:float=1.0;information_gain:float=.25;causal_consistency:float=.25;progress:float=.20;calibration_gain:float=.15;contradiction:float=.50;compute_cost:float=.10;risk:float=.50
    def score(self,r): return self.task*r.task+self.information_gain*r.information_gain+self.causal_consistency*r.causal_consistency+self.progress*r.progress+self.calibration_gain*r.calibration_gain-self.contradiction*r.contradiction-self.compute_cost*r.compute_cost-self.risk*r.risk
class RPEngine:
    def __init__(self,weights=None): self.weights=weights or RewardWeights()
    def observed(self,reward): return self.weights.score(reward)
    def prediction_error(self,predicted_reward,reward): return self.observed(reward)-float(predicted_reward)
