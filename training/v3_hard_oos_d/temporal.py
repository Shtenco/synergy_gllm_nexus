from dataclasses import dataclass
@dataclass(frozen=True)
class TemporalScenario:
    ownership:tuple[tuple[int,int|None,str],...]; blocked:tuple[int,int]
    @classmethod
    def example(cls): return cls(((10,40,'anna'),(40,None,'boris')),(30,40))
    def query(self,t):
        for a,b,v in self.ownership:
            if a<=t and (b is None or t<b): return v
    def rule_enabled(self,t): return not (self.blocked[0]<=t<self.blocked[1])
