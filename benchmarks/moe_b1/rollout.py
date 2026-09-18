from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from nexus_gllm.unified_v3.moe.exact_experts import *
EXPERTS=('r7l','r72','r76','r78','r710','r714','r718')
LINEAGE={'r7l':'r7_fast','r72':'r7_fast','r76':'r7_sem','r78':'r7_proof','r710':'r7_proof','r714':'r7_lang','r718':'r7_late'}
@dataclass(frozen=True)
class Rollout:
    case:object;answers:dict[str,str|None]
    def utilities(self):return tuple(1.0 if self.answers[e]==self.case.gold else (-1.0 if self.answers[e] is not None else 0.0) for e in EXPERTS)
class ExactExpertFederation:
    def __init__(self,root:Path):
        self.r7l=R7LCollectiveExactExpert([root/'r7_seed711.pt',root/'r7_seed712.pt',root/'r7_seed713.pt']);self.r72=R72ExactExpert(root/'r72_language_binder.pt',root/'r7l_core_seed712.pt');self.r76=R76ExactExpert(root/'r76_semantic_knowledge_organ.pkl.bin');self.r78=R78ExactExpert();self.r710=R710ExactExpert();self.r714=R714ExactExpert();self.r718=R718ExactExpert()
    def rollout(self,c):
        a={e:None for e in EXPERTS}
        if 'query_state' in c.payload:a['r7l']=str(self.r7l.predict(c.payload['support'],c.payload['query_state'],c.payload['intent']))
        if 'query' in c.payload:
            try:a['r72']=self.r72.predict(c.payload['support'],c.payload['query'])
            except Exception:pass
        if c.text:
            try:a['r76']=self.r76.answer(c.text)
            except Exception:pass
            try:a['r714']=self.r714.analyze(c.text)[0]
            except Exception:pass
        if c.options:
            item={'id':c.case_id,'domain':'b1','q':c.text,'options':c.options}
            try:a['r78']=self.r78.answer(item)
            except Exception:pass
            try:a['r710']=self.r710.answer(item).get('answer')
            except Exception:pass
            try:
                rows=c.payload.get('teacher_rows')
                out=self.r718.answer(item,rows);a['r718']=out.get('answer')
            except Exception:pass
        return Rollout(c,a)
    def rollout_many(self,cases):return tuple(self.rollout(c) for c in cases)
