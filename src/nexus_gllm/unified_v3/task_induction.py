from dataclasses import dataclass
from .contracts import TaskOpcode,TaskProgram
@dataclass(frozen=True)
class TaskExample: query_operator: str; expected_kind: str
class TaskInducer:
    MAP={'relation_truth':TaskOpcode.QUERY_RELATION,'minimal_proof':TaskOpcode.FIND_MINIMAL_PROOF,'current_state':TaskOpcode.CURRENT_STATE,'historical_state':TaskOpcode.HISTORICAL_STATE,'epistemic_status':TaskOpcode.EPISTEMIC_STATUS,'counterfactual':TaskOpcode.COUNTERFACTUAL_QUERY}
    def induce(self,examples):
        if not examples: raise ValueError('underdetermined task schema')
        kinds={e.expected_kind for e in examples}
        if len(kinds)==1 and next(iter(kinds)) in self.MAP: return TaskProgram(self.MAP[next(iter(kinds))],operator_id=examples[0].query_operator)
        raise ValueError('underdetermined task schema')
