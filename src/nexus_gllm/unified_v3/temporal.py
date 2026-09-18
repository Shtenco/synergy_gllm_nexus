from dataclasses import dataclass,replace
from .contracts import FactVersion,FactLifecycle
@dataclass(frozen=True)
class TemporalLedger:
    versions:tuple[FactVersion,...]=()
    def assert_fact(self,relation,subject,value,time,supersede=False):
        vs=list(self.versions); sup=None
        if supersede:
            for i,v in enumerate(vs):
                if v.relation==relation and v.subject==subject and v.lifecycle is FactLifecycle.ACTIVE:
                    vs[i]=replace(v,valid_until=time,lifecycle=FactLifecycle.SUPERSEDED); sup=i
        vs.append(FactVersion(relation,subject,value,time,None,FactLifecycle.ACTIVE,sup))
        return TemporalLedger(tuple(vs))
    def current(self,relation,subject):
        xs=[v for v in self.versions if v.relation==relation and v.subject==subject and v.lifecycle is FactLifecycle.ACTIVE]
        return max(xs,key=lambda v:v.valid_from) if xs else None
    def at(self,relation,subject,time):
        xs=[v for v in self.versions if v.relation==relation and v.subject==subject and v.valid_from<=time and (v.valid_until is None or time<v.valid_until)]
        return max(xs,key=lambda v:v.valid_from) if xs else None
