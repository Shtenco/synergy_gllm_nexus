from __future__ import annotations
import argparse,hashlib,json,random,time
from collections import Counter
from pathlib import Path
import torch
import torch.nn.functional as F
from nexus_gllm.semantic_relation import SemanticRelationCortex,hard_supcon_loss,hard_weight_matrix
from .omega14_dataset import RELATIONS,load_stage_rows,load_eval_rows,transform_train,collate_semantic,assert_selection_safe

CLASS_COUNTS=torch.tensor([40000.,20000.,10000.,5000.,10000.,10000.])
CLASS_WEIGHTS=(CLASS_COUNTS.sum()/CLASS_COUNTS).sqrt(); CLASS_WEIGHTS=CLASS_WEIGHTS/CLASS_WEIGHTS.mean()

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def loss_bundle(model,out,labels,nota):
    known=labels>=0
    zero=out['scores'].sum()*0
    if known.any():
        w=CLASS_WEIGHTS.to(out['scores'].device)
        ce=F.cross_entropy(out['scores'][known],labels[known],weight=w)
        z=out['z'][known]; y=labels[known]
        hw=hard_weight_matrix(y)
        con=hard_supcon_loss(z,y,hw,temperature=.12)
        proto=out['prototypes'][y]
        pull=(1-(z*proto).sum(-1)).mean()
        true=out['scores'][known].gather(1,y[:,None]).squeeze(1)
        masked=out['scores'][known].clone(); masked.scatter_(1,y[:,None],-1e9)
        other=masked.max(1).values
        margin=F.relu(.35-(true-other)).mean()
    else: ce=con=pull=margin=zero
    nota_loss=F.binary_cross_entropy_with_logits(out['nota_logit'],nota.to(out['nota_logit'].dtype))
    geom=model.geometry_loss()
    loss=ce+.12*con+.12*pull+.08*margin+.45*nota_loss+.08*geom
    return {'loss':loss,'ce':ce,'contrastive':con,'prototype_pull':pull,'margin':margin,'nota':nota_loss,'geometry':geom}

def _f1_for_label(gold,pred,label):
    tp=sum(g==label and p==label for g,p in zip(gold,pred)); fp=sum(g!=label and p==label for g,p in zip(gold,pred)); fn=sum(g==label and p!=label for g,p in zip(gold,pred))
    pr=tp/(tp+fp) if tp+fp else 0.; rc=tp/(tp+fn) if tp+fn else 0.; f=2*pr*rc/(pr+rc) if pr+rc else 0.
    return pr,rc,f

def metrics_from_predictions(gold,pred):
    labels=RELATIONS+['abstain']
    acc=sum(g==p for g,p in zip(gold,pred))/max(1,len(gold))
    fs=[_f1_for_label(gold,pred,l)[2] for l in labels]
    p,r,f=_f1_for_label(gold,pred,'abstain')
    known=[i for i,g in enumerate(gold) if g!='abstain']
    kacc=sum(gold[i]==pred[i] for i in known)/max(1,len(known))
    return {'accuracy':acc,'known_accuracy':kacc,'macro_f1':sum(fs)/len(fs),'nota_precision':p,'nota_recall':r,'nota_f1':f}

@torch.no_grad()
def evaluate(model,rows,batch_size=1024,nota_threshold=.5,device='cpu'):
    model.eval(); gold=[]; pred=[]
    for st in range(0,len(rows),batch_size):
        b=rows[st:st+batch_size]; flat,offs,rules,labels,nota=collate_semantic(b,model.hash_buckets)
        flat,offs,rules=flat.to(device),offs.to(device),rules.to(device)
        out=model(flat,offs,rules); rel=out['scores'].argmax(1).cpu(); np=torch.sigmoid(out['nota_logit']).cpu()
        for i,r in enumerate(b):
            g=r['relation']; p='abstain' if float(np[i])>=nota_threshold else RELATIONS[int(rel[i])]
            gold.append(g); pred.append(p)
    m=metrics_from_predictions(gold,pred); m['nota_threshold']=nota_threshold
    return m

def tune_nota_threshold(model,rows,device='cpu'):
    best=None
    for t in [i/100 for i in range(20,86,5)]:
        m=evaluate(model,rows,nota_threshold=t,device=device)
        key=(m['macro_f1'],m['accuracy'])
        if best is None or key>best[0]:best=(key,t,m)
    return best[1],best[2]

def train(train_path,shadow_path,out_path,limit=None,epochs=3,batch_size=512,lr=8e-4,seed=17,device='cpu'):
    assert_selection_safe(train_path); assert_selection_safe(shadow_path)
    random.seed(seed); torch.manual_seed(seed); torch.set_num_threads(min(5,torch.get_num_threads()))
    base=load_stage_rows(train_path,'train')
    if limit: base=base[:limit]
    stage_dev=load_stage_rows(train_path,'dev')
    dev=[]
    from nexus_gllm.semantic_features import mask_arguments
    for r in stage_dev:
        t=r['compiler_target']; s=t.get('subject_text'); o=t.get('object_text')
        dev.append({'id':r['id'],'relation':t['relation'],'input_text':r['input_text'],'masked_text':mask_arguments(r['input_text'],s,o),'subject_text':s,'object_text':o})
    shadow=load_eval_rows(shadow_path)
    model=SemanticRelationCortex().to(device); opt=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=.01)
    best=None; history=[]
    for ep in range(epochs):
        model.train(); order=list(range(len(base))); random.Random(seed+ep).shuffle(order); sums=Counter(); nbat=0; t0=time.time()
        for st in range(0,len(order),batch_size):
            batch=[transform_train(base[j],epoch_seed=ep) for j in order[st:st+batch_size]]
            flat,offs,rules,labels,nota=collate_semantic(batch,model.hash_buckets)
            flat,offs,rules,labels,nota=[x.to(device) for x in (flat,offs,rules,labels,nota)]
            out=model(flat,offs,rules); parts=loss_bundle(model,out,labels,nota)
            opt.zero_grad(); parts['loss'].backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step()
            for k,v in parts.items():sums[k]+=float(v.detach())
            nbat+=1
        th,shadow_m=tune_nota_threshold(model,shadow,device)
        dev_m=evaluate(model,dev,nota_threshold=th,device=device)
        rec={'epoch':ep+1,'seconds':time.time()-t0,'threshold':th,'train':{k:v/max(1,nbat) for k,v in sums.items()},'dev':dev_m,'shadow':shadow_m}
        history.append(rec); print(json.dumps(rec,ensure_ascii=False),flush=True)
        score=(shadow_m['macro_f1'],shadow_m['accuracy'],dev_m['macro_f1'])
        if best is None or score>best[0]:
            best=(score,ep+1,th,{k:v.detach().cpu().clone() for k,v in model.state_dict().items()},dev_m,shadow_m)
    model.load_state_dict(best[3]); payload={'format_version':1,'architecture':'omega14_semantic_operator_cortex','config':{'hash_buckets':model.hash_buckets,'embed_dim':model.embed_dim,'rule_dim':model.rule_dim},'seed':seed,'selected_epoch':best[1],'nota_threshold':best[2],'dev_metrics':best[4],'shadow_metrics':best[5],'history':history,'state_dict':model.state_dict(),'train_corpus_sha256':sha256(train_path),'shadow_sha256':sha256(shadow_path),'blind_metrics':None}
    Path(out_path).parent.mkdir(parents=True,exist_ok=True); torch.save(payload,out_path)
    return payload
