from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass

@dataclass(frozen=True)
class PendingSlotFrame:
    goal_id: str
    topic: str
    payload: dict

@dataclass(frozen=True)
class AnaphoraResolution:
    entity_id: str|None
    clarification_required: bool
    candidates: tuple[str,...]=()

@dataclass(frozen=True)
class _EntityMention:
    entity_id: str
    label: str
    gender: str|None

class ContextCortexV2:
    """Rebuilt context contract inspired by R7.44.3, never claimed EXACT."""
    source_status='REBUILT_FROM_R7.44.3_CONTRACTS'

    def __init__(self):
        self._facts=defaultdict(list)
        self._stale=defaultdict(list)
        self._pending: dict[tuple[str,str],PendingSlotFrame]={}
        self._mentions=defaultdict(lambda: deque(maxlen=16))
        self.current_topic='default'

    def remember(self,key,value,*,topic='default',revision=False):
        bucket=self._facts[(topic,key)]
        if revision and bucket:
            self._stale[(topic,key)].append(bucket[-1])
        bucket.append(value)
        return value

    def recall(self,key,*,topic='default'):
        bucket=self._facts.get((topic,key),())
        return bucket[-1] if bucket else None

    def history(self,key,*,topic='default'):
        return tuple(self._facts.get((topic,key),()))

    def stale_values(self,key,*,topic='default'):
        return tuple(self._stale.get((topic,key),()))

    def suspend_goal(self,goal_id,payload,*,topic='default'):
        self._pending[(topic,goal_id)]=PendingSlotFrame(goal_id,topic,dict(payload))

    def resume_goal(self,goal_id,*,topic='default'):
        x=self._pending.get((topic,goal_id))
        return dict(x.payload) if x is not None else None

    def complete_goal(self,goal_id,*,topic='default'):
        return self._pending.pop((topic,goal_id),None)

    def hard_boundary(self,topic: str):
        self.current_topic=topic
        # Boundary prevents accidental anaphora carryover; stored facts stay topic-scoped.
        self._mentions[topic].clear()

    def mention_entity(self,entity_id: str,label: str,*,gender: str|None=None,topic='default'):
        m=_EntityMention(entity_id,label,gender); self._mentions[topic].append(m); return m

    def resolve_anaphora(self,token: str,*,topic='default')->AnaphoraResolution:
        low=token.casefold().strip(' .,!?:;')
        gender={'она':'f','её':'f','ей':'f','он':'m','его':'m','ему':'m'}.get(low)
        mentions=list(self._mentions.get(topic,()))
        if gender is not None:
            candidates=[m for m in mentions if m.gender in (gender,None)]
        else:
            candidates=mentions
        # Deduplicate by entity while preserving recency.
        uniq=[]; seen=set()
        for m in reversed(candidates):
            if m.entity_id not in seen: uniq.append(m); seen.add(m.entity_id)
        if len(uniq)==1:
            return AnaphoraResolution(uniq[0].entity_id,False,(uniq[0].entity_id,))
        return AnaphoraResolution(None,True,tuple(m.entity_id for m in uniq))
