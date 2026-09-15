from __future__ import annotations
import argparse, json, random, time
from pathlib import Path
import torch
from nexus_gllm.semantic_relation import SemanticRelationCortex
from nexus_gllm.semantic_features import mask_arguments
from .omega14_dataset import load_stage_rows,load_eval_rows,transform_train,collate_semantic,assert_selection_safe
from .train_omega14 import loss_bundle,evaluate,tune_nota_threshold,sha256

def build_dev(rows):
    out=[]
    for r in rows:
        t=r['compiler_target']; s=t.get('subject_text'); o=t.get('object_text')
        out.append({'id':r['id'],'relation':t['relation'],'input_text':r['input_text'],'masked_text':mask_arguments(r['input_text'],s,o),'subject_text':s,'object_text':o})
    return out

def run_chunk(train_path,shadow_path,state_path,best_path,chunk_examples=20480,batch_size=512,lr=8e-4,seed=17,device='cpu'):
    assert_selection_safe(train_path); assert_selection_safe(shadow_path)
    torch.set_num_threads(min(5,torch.get_num_threads())); random.seed(seed); torch.manual_seed(seed)
    train_rows=load_stage_rows(train_path,'train'); dev=build_dev(load_stage_rows(train_path,'dev')); shadow=load_eval_rows(shadow_path)
    perm=list(range(len(train_rows))); random.Random(seed).shuffle(perm)
    model=SemanticRelationCortex().to(device); opt=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=.01)
    state_p=Path(state_path)
    if state_p.exists():
        st=torch.load(state_p,map_location=device,weights_only=False)
        if st['train_sha256']!=sha256(train_path) or st['shadow_sha256']!=sha256(shadow_path): raise RuntimeError('corpus SHA mismatch')
        model.load_state_dict(st['model']); opt.load_state_dict(st['optimizer']); cursor=st['cursor']; history=st['history']; best=st['best']
    else:
        cursor=0; history=[]; best=None
    end=min(len(perm),cursor+chunk_examples); model.train(); sums={}; nbat=0; t0=time.time()
    for st_i in range(cursor,end,batch_size):
        ids=perm[st_i:min(end,st_i+batch_size)]
        batch=[transform_train(train_rows[j],epoch_seed=0) for j in ids]
        flat,offs,rules,labels,nota=collate_semantic(batch,model.hash_buckets)
        flat,offs,rules,labels,nota=[x.to(device) for x in (flat,offs,rules,labels,nota)]
        out=model(flat,offs,rules); parts=loss_bundle(model,out,labels,nota)
        opt.zero_grad(); parts['loss'].backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step()
        for k,v in parts.items(): sums[k]=sums.get(k,0.0)+float(v.detach())
        nbat+=1
    threshold,shadow_m=tune_nota_threshold(model,shadow,device); dev_m=evaluate(model,dev,nota_threshold=threshold,device=device)
    rec={'cursor':end,'seen':end,'seconds':time.time()-t0,'threshold':threshold,'train':{k:v/max(1,nbat) for k,v in sums.items()},'dev':dev_m,'shadow':shadow_m}
    history.append(rec)
    score=(shadow_m['macro_f1'],shadow_m['accuracy'],dev_m['macro_f1'],dev_m['accuracy'])
    if best is None or tuple(best['score'])<score:
        best={'score':list(score),'cursor':end,'threshold':threshold,'dev':dev_m,'shadow':shadow_m,'model':{k:v.detach().cpu().clone() for k,v in model.state_dict().items()}}
        torch.save({'format_version':1,'architecture':'omega14_semantic_operator_cortex','config':{'hash_buckets':model.hash_buckets,'embed_dim':model.embed_dim,'rule_dim':model.rule_dim},'selected_cursor':end,'nota_threshold':threshold,'dev_metrics':dev_m,'shadow_metrics':shadow_m,'state_dict':best['model'],'train_sha256':sha256(train_path),'shadow_sha256':sha256(shadow_path),'blind_metrics':None},best_path)
    torch.save({'model':model.state_dict(),'optimizer':opt.state_dict(),'cursor':end,'history':history,'best':best,'train_sha256':sha256(train_path),'shadow_sha256':sha256(shadow_path),'seed':seed,'lr':lr},state_path)
    print(json.dumps(rec,ensure_ascii=False)); return rec

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('train');ap.add_argument('shadow');ap.add_argument('--state',required=True);ap.add_argument('--best',required=True);ap.add_argument('--chunk-examples',type=int,default=20480);ap.add_argument('--batch-size',type=int,default=512);ap.add_argument('--lr',type=float,default=8e-4);a=ap.parse_args()
    run_chunk(a.train,a.shadow,a.state,a.best,a.chunk_examples,a.batch_size,a.lr)
if __name__=='__main__':main()
