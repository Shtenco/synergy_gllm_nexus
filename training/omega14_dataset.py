from __future__ import annotations
import gzip,json,hashlib,re
from nexus_gllm.semantic_features import mask_arguments,batch_features

RELATIONS=['owned_by','located_in','is_a','older_than','before','causes']
TRAIN_BANK={
'owned_by':["{S} принадлежит {O}.","У {O} есть {S}.","Собственник {S} — {O}."],
'located_in':["{S} находится в {O}.","{S} расположен в {O}.","В {O} находится {S}."],
'is_a':["{S} является {O}.","{S} относится к классу {O}.","Класс объекта {S} — {O}."],
'older_than':["{S} старше {O}.","{O} младше {S}.","Возраст {S} больше возраста {O}."],
'before':["Сначала {S}, потом {O}.","{S} произошло до {O}.","После {S} произошло {O}."],
'causes':["{S}, поэтому {O}.","{S} вызвало {O}.","{O} произошло из-за {S}."],
'abstain':["Возможно, {S} связано с {O}, но данных недостаточно.","{S} и {O} упомянуты вместе, однако тип связи не указан.","Нельзя подтвердить, что {S} принадлежит {O}."],
}

def assert_selection_safe(path):
    s=str(path).lower()
    if 'blind2' in s: raise ValueError('Blind-2 is forbidden during training/model selection')

def _entity_pair(row):
    t=row['compiler_target']; s=t.get('subject_text'); o=t.get('object_text')
    if s and o:return s,o
    vals=re.findall(r'[A-Za-zА-Яа-я0-9_]+_\d+',row['input_text'])
    if len(vals)>=2:return vals[0],vals[1]
    h=hashlib.sha256(row['id'].encode()).hexdigest()[:8]
    return f'tr_сущность_{h}',f'tr_цель_{h}'

def transform_train(row,epoch_seed=0):
    rel=row['compiler_target']['relation']; s,o=_entity_pair(row)
    idx=int.from_bytes(hashlib.blake2b(f"{row['id']}|{epoch_seed}".encode(),digest_size=8).digest(),'little')%len(TRAIN_BANK[rel])
    text=TRAIN_BANK[rel][idx].format(S=s,O=o)
    masked=mask_arguments(text,s,o)
    return {'id':row['id'],'relation':rel,'input_text':text,'masked_text':masked,'subject_text':None if rel=='abstain' else s,'object_text':None if rel=='abstain' else o}

def load_stage_rows(path,split):
    assert_selection_safe(path)
    out=[]
    with gzip.open(path,'rt',encoding='utf8') as f:
        for line in f:
            r=json.loads(line)
            if r['split']==split: out.append(r)
    return out

def load_eval_rows(path):
    assert_selection_safe(path)
    out=[]
    with gzip.open(path,'rt',encoding='utf8') as f:
        for line in f:
            r=json.loads(line)
            s=r.get('subject_text'); o=r.get('object_text')
            out.append({'id':r['id'],'relation':r['relation'],'input_text':r['input_text'],'masked_text':mask_arguments(r['input_text'],s,o),'subject_text':s,'object_text':o})
    return out

def collate_semantic(rows,buckets=4096):
    texts=[r['masked_text'] for r in rows]
    flat,offs,rules=batch_features(texts,buckets)
    labels=[]; nota=[]
    for r in rows:
        if r['relation']=='abstain': labels.append(-1); nota.append(1.)
        else: labels.append(RELATIONS.index(r['relation'])); nota.append(0.)
    import torch
    return flat,offs,rules,torch.tensor(labels),torch.tensor(nota)
