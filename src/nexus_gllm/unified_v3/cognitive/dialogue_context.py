from __future__ import annotations
from dataclasses import dataclass,replace
from enum import Enum

class ContextValueStatus(str,Enum):
    ASSERTED='ASSERTED'
    VERIFIED='VERIFIED'
    SUPERSEDED='SUPERSEDED'

@dataclass(frozen=True)
class ContextValue:
    key:str
    value:str
    status:ContextValueStatus
    turn:int
    provenance_id:str=''
    supersedes_turn:int|None=None

@dataclass(frozen=True)
class PendingSlot:
    frame_id:str
    slot_name:str
    opened_turn:int
    expected_type:str=''
    required:bool=True

@dataclass(frozen=True)
class Referent:
    mention:str
    entity_id:str
    turn:int
    confidence:float=1.0

@dataclass(frozen=True)
class DialogueContextState:
    session_id:str
    boundary_id:int=0
    turn:int=0
    values:tuple[ContextValue,...]=()
    pending_slots:tuple[PendingSlot,...]=()
    referents:tuple[Referent,...]=()
    trace:tuple[str,...]=()

class DialogueContextR1:
    """New CRC context manager. It is not an exact reconstruction of R7.44.3."""
    def __init__(self,session_id):
        self.state=DialogueContextState(session_id)

    def _advance(self,event):
        self.state=replace(self.state,turn=self.state.turn+1,trace=self.state.trace+(event,))
        return self.state

    def hard_boundary(self,reason='explicit'):
        self._advance('hard_boundary:'+reason)
        self.state=replace(self.state,boundary_id=self.state.boundary_id+1,pending_slots=(),referents=())
        return self.state

    def mention(self,mention,entity_id,confidence=1.0):
        self._advance('mention')
        r=Referent(mention.casefold(),entity_id,self.state.turn,float(confidence))
        self.state=replace(self.state,referents=self.state.referents+(r,))
        return r

    def resolve(self,mention,min_confidence=.5):
        m=mention.casefold()
        rows=[r for r in self.state.referents if r.mention==m and r.confidence>=min_confidence]
        return max(rows,key=lambda r:(r.turn,r.confidence,r.entity_id)) if rows else None

    def open_slot(self,frame_id,slot_name,expected_type='',required=True):
        self._advance('open_slot:'+slot_name)
        s=PendingSlot(frame_id,slot_name,self.state.turn,expected_type,bool(required))
        existing=tuple(x for x in self.state.pending_slots if not (x.frame_id==frame_id and x.slot_name==slot_name))
        self.state=replace(self.state,pending_slots=existing+(s,))
        return s

    def fill_slot(self,frame_id,slot_name,value,*,status=ContextValueStatus.ASSERTED,provenance_id=''):
        matches=[s for s in self.state.pending_slots if s.frame_id==frame_id and s.slot_name==slot_name]
        if not matches:raise KeyError('pending slot not found')
        self._advance('fill_slot:'+slot_name)
        self.state=replace(self.state,pending_slots=tuple(s for s in self.state.pending_slots if s not in matches))
        return self.set_value(f'{frame_id}.{slot_name}',value,status=status,provenance_id=provenance_id,advance=False)

    def set_value(self,key,value,*,status=ContextValueStatus.ASSERTED,provenance_id='',advance=True):
        if advance:self._advance('set_value:'+key)
        active=[v for v in self.state.values if v.key==key and v.status is not ContextValueStatus.SUPERSEDED]
        # A lower-authority assertion cannot overwrite a verified active fact.
        if status is ContextValueStatus.ASSERTED and any(v.status is ContextValueStatus.VERIFIED for v in active):
            self.state=replace(self.state,trace=self.state.trace+('assertion_blocked_by_verified:'+key,))
            return max((v for v in active if v.status is ContextValueStatus.VERIFIED),key=lambda x:x.turn)
        values=list(self.state.values);sup_turn=None
        for old in active:
            idx=values.index(old);values[idx]=replace(old,status=ContextValueStatus.SUPERSEDED);sup_turn=max(sup_turn or 0,old.turn)
        new=ContextValue(key,str(value),status,self.state.turn,provenance_id,sup_turn)
        values.append(new);self.state=replace(self.state,values=tuple(values));return new

    def current(self,key):
        rows=[v for v in self.state.values if v.key==key and v.status is not ContextValueStatus.SUPERSEDED]
        if not rows:return None
        return max(rows,key=lambda v:((1 if v.status is ContextValueStatus.VERIFIED else 0),v.turn))

    def unresolved_required_slots(self):
        return tuple(s for s in self.state.pending_slots if s.required)
