from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .state import NexusCognitiveState
from .memory import HierarchicalMemoryStore
from .program_ast import ProgramSynthesizer
from .reward import RPEngine,RewardVector
from .credit import CognitiveTraceGraph
from .credit_learning import RecursiveCreditLearner
from .self_model import NexusSelfModel
from .meta_controller import MetaController
from .continual import ContinualLearningPolicy
@dataclass(frozen=True)
class CognitiveOutcome:
    state:NexusCognitiveState;answer:Any;reward:float;rpe:float;credit:dict[str,float]
class CognitiveRecursiveCoreR1:
    def __init__(self):
        self.memory=HierarchicalMemoryStore();self.programs=ProgramSynthesizer();self.meta=MetaController();self.rpe=RPEngine();self.self_model=NexusSelfModel();self.credit_learner=RecursiveCreditLearner(self.self_model);self.continual=ContinualLearningPolicy()
    def close_episode(self,state,*,answer,reward,trace_graph,outcome_node_id,counterfactual_credit=None):
        observed=self.rpe.observed(reward);delta=observed-state.predicted_reward;credit=self.credit_learner.update(trace_graph,outcome_node_id,delta,counterfactual_credit=counterfactual_credit)
        final=state.transition('outcome',ref_id=outcome_node_id,data={'rpe':delta},observed_reward=observed)
        return CognitiveOutcome(final,answer,observed,delta,credit)
