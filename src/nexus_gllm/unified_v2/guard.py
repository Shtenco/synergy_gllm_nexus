from __future__ import annotations
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class GuardResult:
    ok: bool
    violations: tuple[str,...]

class SemanticConsistencyGuard:
    def _licensed_tokens(self,answer_graph):
        toks=set()
        nums=set()
        for c in answer_graph.claims:
            vals=[c.subject.canonical_name,c.relation]
            if hasattr(c.object,'canonical_name'): vals.append(c.object.canonical_name)
            else: vals.append(str(c.object))
            for v in vals:
                toks.update(re.findall(r'[\w-]+',str(v).casefold(),re.UNICODE))
                nums.update(re.findall(r'\d+(?:[.,]\d+)?',str(v)))
        return toks,nums
    def check(self,answer_graph,text:str):
        licensed,licensed_nums=self._licensed_tokens(answer_graph)
        words=set(re.findall(r'[\w-]+',text.casefold(),re.UNICODE))
        nums=set(re.findall(r'\d+(?:[.,]\d+)?',text))
        violations=[]
        if nums-licensed_nums: violations.append('unlicensed_number')
        graph_negative=any(c.polarity=='negative' for c in answer_graph.claims)
        if ('не' in words or 'нет' in words) and not graph_negative: violations.append('negation_flip')
        cap=set(re.findall(r'\b[А-ЯЁA-Z][\w-]+',text,re.UNICODE))
        licensed_caps={t.casefold() for t in licensed}
        unknown=[x for x in cap if x.casefold() not in licensed_caps]
        if unknown: violations.append('unlicensed_entity')
        return GuardResult(not violations,tuple(sorted(set(violations))))
