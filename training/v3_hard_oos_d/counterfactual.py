from dataclasses import dataclass
@dataclass(frozen=True)
class CounterfactualTrap:
    actual:bool=True
    @classmethod
    def example(cls): return cls(True)
    def apply(self,intervention):
        if intervention=='necessary': return False
        return True
