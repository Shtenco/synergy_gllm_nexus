from dataclasses import dataclass
from .contracts import TaskOpcode,TaskProgram
@dataclass(frozen=True)
class TaskExample:
    query_operator: str
    expected_kind: str
class TaskInducer:
    def induce(self,examples):
        if examples and all(e.expected_kind=='relation_truth' for e in examples):
            return TaskProgram(TaskOpcode.QUERY_RELATION,operator_id=examples[0].query_operator)
        raise ValueError('underdetermined task schema')
