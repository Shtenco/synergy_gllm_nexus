from __future__ import annotations
import hashlib,re
from .types import ClaimProposal,SourceRecord

_PATTERNS=[
    (re.compile(r'(?P<s>[A-ZА-ЯЁ][\wА-Яа-яЁё_-]*(?:\s+[\wА-Яа-яЁё_-]+){0,5})\s+принадлежит\s+(?P<o>[A-ZА-ЯЁ][\wА-Яа-яЁё_-]*(?:\s+[\wА-Яа-яЁё_-]+){0,5})',re.I),'owned_by'),
    (re.compile(r'(?P<s>[A-ZА-ЯЁ][\wА-Яа-яЁё_-]*(?:\s+[\wА-Яа-яЁё_-]+){0,5})\s+(?:находится|расположен[ао]?)\s+в\s+(?P<o>[A-ZА-ЯЁ][\wА-Яа-яЁё_-]*(?:\s+[\wА-Яа-яЁё_-]+){0,5})',re.I),'located_in'),
    (re.compile(r'(?P<s>[A-ZА-ЯЁ][\wА-Яа-яЁё_-]*(?:\s+[\wА-Яа-яЁё_-]+){0,5})\s+(?:является|это)\s+(?P<o>[A-ZА-ЯЁ][\wА-Яа-яЁё_-]*(?:\s+[\wА-Яа-яЁё_-]+){0,5})',re.I),'is_a'),
]

class ClaimExtractor:
    def __init__(self,graph_extractor=None): self.graph_extractor=graph_extractor
    def extract(self,source:SourceRecord):
        if self.graph_extractor is not None:
            try:
                out=self.graph_extractor(source.content)
                if out:return out
            except Exception: pass
        claims=[]
        for sent in re.split(r'(?<=[.!?])\s+',source.content):
            for rx,rel in _PATTERNS:
                m=rx.search(sent)
                if not m: continue
                txt=m.group(0).strip(); cid=hashlib.sha256((source.source_id+'\0'+txt+'\0'+rel).encode()).hexdigest()[:24]
                claims.append(ClaimProposal(cid,m.group('s').strip(),rel,m.group('o').strip(' .'),txt,txt,source.source_id,.7))
        return claims