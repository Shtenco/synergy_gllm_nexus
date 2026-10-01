from __future__ import annotations
from dataclasses import dataclass,replace
from enum import Enum
import hashlib,json

class BeliefStatus(str,Enum):
    PROPOSED='PROPOSED'
    ASSERTED='ASSERTED'
    VERIFIED='VERIFIED'
    REJECTED='REJECTED'
    CONFLICTED='CONFLICTED'
    SUPERSEDED='SUPERSEDED'

@dataclass(frozen=True)
class Belief:
    belief_id:str
    proposition_key:str
    value:str
    polarity:bool
    status:BeliefStatus
    confidence:float
    provenance_ids:tuple[str,...]=()
    parent_ids:tuple[str,...]=()
    revision:int=1

@dataclass(frozen=True)
class BeliefResolution:
    proposition_key:str
    status:BeliefStatus
    active:tuple[Belief,...]
    preferred:Belief|None=None

class BeliefLedger:
    """Versioned epistemic ledger; contradiction is represented, never overwritten."""
    def __init__(self):self._by_key={};self._by_id={}

    @staticmethod
    def _id(key,value,polarity,revision,parents):
        body=json.dumps([key,value,bool(polarity),revision,list(parents)],ensure_ascii=False,separators=(',',':'))
        return 'belief:'+hashlib.sha256(body.encode()).hexdigest()[:24]

    def add(self,key,value,*,polarity=True,status=BeliefStatus.PROPOSED,confidence=.5,provenance_ids=(),parent_ids=()):
        if not 0<=confidence<=1:raise ValueError('confidence must be in [0,1]')
        hist=self._by_key.setdefault(key,[])
        revision=1+max((b.revision for b in hist),default=0)
        bid=self._id(key,value,polarity,revision,parent_ids)
        b=Belief(bid,key,value,bool(polarity),status,float(confidence),tuple(provenance_ids),tuple(parent_ids),revision)
        hist.append(b);self._by_id[bid]=b;return b

    def get(self,belief_id):return self._by_id[belief_id]
    def history(self,key):return tuple(self._by_key.get(key,()))

    def supersede(self,old_id,new_value,*,status=BeliefStatus.ASSERTED,confidence=.5,provenance_ids=()):
        old=self.get(old_id)
        marked=replace(old,status=BeliefStatus.SUPERSEDED)
        hist=self._by_key[old.proposition_key]
        hist[hist.index(old)]=marked;self._by_id[old_id]=marked
        return self.add(old.proposition_key,new_value,polarity=old.polarity,status=status,confidence=confidence,provenance_ids=provenance_ids,parent_ids=(old_id,))

    def resolve(self,key):
        active=tuple(b for b in self._by_key.get(key,()) if b.status not in (BeliefStatus.REJECTED,BeliefStatus.SUPERSEDED))
        if not active:return BeliefResolution(key,BeliefStatus.REJECTED,())
        verified=tuple(b for b in active if b.status is BeliefStatus.VERIFIED)
        signatures={(b.value,b.polarity) for b in verified}
        if len(signatures)>1:return BeliefResolution(key,BeliefStatus.CONFLICTED,active,None)
        if len(signatures)==1:
            pref=max(verified,key=lambda b:(b.confidence,b.revision,b.belief_id))
            return BeliefResolution(key,BeliefStatus.VERIFIED,active,pref)
        asserted=tuple(b for b in active if b.status is BeliefStatus.ASSERTED)
        sig={(b.value,b.polarity) for b in asserted}
        if len(sig)>1:return BeliefResolution(key,BeliefStatus.CONFLICTED,active,None)
        if asserted:
            pref=max(asserted,key=lambda b:(b.confidence,b.revision,b.belief_id))
            return BeliefResolution(key,BeliefStatus.ASSERTED,active,pref)
        pref=max(active,key=lambda b:(b.confidence,b.revision,b.belief_id))
        return BeliefResolution(key,BeliefStatus.PROPOSED,active,pref)
