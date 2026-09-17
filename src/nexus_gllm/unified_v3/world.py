from .contracts import WorldFact,WorldHypothesis
class WorldInducer:
    def from_observations(self,observations):
        facts=[]
        for obs in observations:
            for atom in obs.atoms:
                facts.append(WorldFact(atom.operator,atom.arguments,atom.polarity))
        return (WorldHypothesis('world:0',tuple(facts)),)
