import hashlib
from .contracts import *
def world_fingerprint(w):
    rows=sorted((f.operator.operator_id,tuple(x.entity_id for x in f.arguments),f.polarity) for f in w.facts)
    return hashlib.sha256(repr(rows).encode()).hexdigest()
class CounterfactualEngine:
    def apply(self,world,interventions):
        facts=list(world.facts)
        for i in interventions:
            if i.kind is InterventionKind.REMOVE_FACT and i.fact is not None: facts=[f for f in facts if f!=i.fact]
            elif i.kind is InterventionKind.ADD_FACT and i.fact is not None: facts.append(i.fact)
            elif i.kind is InterventionKind.FLIP_POLARITY and i.fact is not None:
                facts=[WorldFact(f.operator,f.arguments,not f.polarity) if f==i.fact else f for f in facts]
        return WorldHypothesis(world.world_id+':cf',tuple(facts),parent_world_id=world.world_id)
