from .contracts import ConflictSet,ConflictResolution
class ConflictEngine:
    def resolve(self,support):
        pos=tuple(src for src,val in support if val); neg=tuple(src for src,val in support if not val)
        if pos and neg: r=ConflictResolution.CONFLICTED
        elif pos: r=ConflictResolution.RESOLVED_POSITIVE
        elif neg: r=ConflictResolution.RESOLVED_NEGATIVE
        else: r=ConflictResolution.UNRESOLVED
        return ConflictSet(pos,neg,r)
