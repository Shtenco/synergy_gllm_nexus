from __future__ import annotations
import hashlib,re
import torch

CUES={
 'owned_by':('принадлеж','собствен','влад','облад','распоряж','хозя','право на','оформ'),
 'located_in':('наход','располаг','располож','размещ','пребыв','мест','локац','стоять'),
 'is_a':('явля','представля','класс','категор','разновид','тип','вид','сорт','групп'),
 'older_than':('старш','старе','младш','молож','возраст','рожд','родил'),
 'before':('сначала','потом','до','после','раньш','перед','затем','предшеств','поздн','вслед за'),
 'causes':('причин','потому','поскольку','из-за','поэтому','следств','вызв','привод','обуслов'),
}
REL_ORDER=('owned_by','located_in','is_a','older_than','before','causes')
NEG=(' не ','нет ','нельзя','опроверг','отверга','недостаточ','неподтвержд','неизвест')
UNCERT=('возможно','предполож','неяс','недостаточ','не определ','нельзя определить','нет оснований')
CONTRAST=('но','однако','хотя','несмотря')

def mask_arguments(text:str,subject:str|None,object_:str|None)->str:
    out=text
    pairs=[(subject,'<SUBJ>'),(object_,'<OBJ>')]
    for value,marker in sorted([(a,b) for a,b in pairs if a],key=lambda x:-len(x[0])):
        out=out.replace(value,marker)
    return re.sub(r'\s+',' ',out).strip()

def hashed_ngrams(text:str,buckets:int=4096,ns=(3,4,5)):
    t='^'+text.lower()+'$'; ids=[]
    for n in ns:
        for i in range(max(0,len(t)-n+1)):
            ids.append(int.from_bytes(hashlib.blake2b(t[i:i+n].encode('utf-8'),digest_size=8).digest(),'little')%buckets)
    return ids or [0]

def _clause_weight(clause:str,index:int,clauses:list[str])->float:
    c=clause.strip().lower()
    if c.startswith('хотя ') or c.startswith('несмотря '): return .28
    if index>0 and (clauses[index-1].strip().lower().startswith('хотя ') or clauses[index-1].strip().lower().startswith('несмотря ')): return 1.45
    if c.startswith('но ') or c.startswith('однако '): return 1.35
    return 1.0

def relation_evidence_scores(text:str)->torch.Tensor:
    t=' '+text.lower()+' '
    clauses=[x for x in re.split(r'[,;]',t) if x.strip()]
    scores={r:0.0 for r in REL_ORDER}
    for i,c in enumerate(clauses):
        w=_clause_weight(c,i,clauses)
        for rel in REL_ORDER:
            for cue in CUES[rel]:
                n=c.count(cue)
                if n:
                    cw=0.35 if (rel=='is_a' and cue=='явля') else (1.25 if (rel=='owned_by' and cue in ('влад','собствен','принадлеж')) else 1.0)
                    scores[rel]+=w*n*cw
        if any(x in c for x in ('причин','следств','вызв','обуслов')): scores['causes']+=.8*w
        if any(x in c for x in ('рожд','родил','возраст','старш','младш','молож')): scores['older_than']+=.8*w
        if any(x in c for x in ('класс','категор','разновид','тип','представля собой')): scores['is_a']+=.5*w
    return torch.tensor([scores[r] for r in REL_ORDER],dtype=torch.float32)

def rule_features(text:str)->torch.Tensor:
    t=' '+text.lower()+' '
    rel=relation_evidence_scores(text).tolist()
    vals=list(rel)
    vals += [float(any(x in t for x in NEG)),float(any(x in t for x in UNCERT)),float(any(x in t for x in CONTRAST))]
    vals += [float(t.find('<subj>') < t.find('<obj>')) if '<subj>' in t and '<obj>' in t else 0.0,float('<subj>' in t),float('<obj>' in t)]
    vals += [float(any(x in t for x in ('раньш','до','перед','предшеств'))),float(any(x in t for x in ('после','потом','затем','поздн'))),float(any(x in t for x in ('поэтому','следств','значит'))),float(any(x in t for x in ('причин','из-за','потому','обуслов'))),float(any(x in t for x in ('старш','больше','выше','рожд','родил'))),float(any(x in t for x in ('младш','меньше','ниже','молож'))),float(len(t.split())/32.0),float(len(t)/128.0)]
    assert len(vals)==20
    return torch.tensor(vals,dtype=torch.float32)

def batch_features(texts,buckets=4096):
    flat=[]; offsets=[]; cursor=0; rules=[]
    for t in texts:
        offsets.append(cursor); ids=hashed_ngrams(t,buckets); flat.extend(ids); cursor+=len(ids); rules.append(rule_features(t))
    return torch.tensor(flat,dtype=torch.long),torch.tensor(offsets,dtype=torch.long),torch.stack(rules)
