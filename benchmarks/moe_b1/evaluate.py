from collections import Counter
from .rollout import EXPERTS,LINEAGE
from .train_router import route_with_scores

def _fuse(r,selected):
    vals=[r.answers[EXPERTS[i]] for i in selected if r.answers[EXPERTS[i]] is not None]
    if not vals:return None
    c=Counter(vals);return sorted(c.items(),key=lambda x:(-x[1],str(x[0])))[0][0]
def learned_fuse(r,selected,scores):
    lineage_counts=Counter(LINEAGE[EXPERTS[i]] for i in selected if r.answers[EXPERTS[i]] is not None);weighted=Counter();best_fallback=None
    for i in selected:
        e=EXPERTS[i];ans=r.answers[e]
        if ans is None:continue
        raw=float(scores[i])
        if best_fallback is None or raw>best_fallback[0]:best_fallback=(raw,ans)
        weighted[ans]+=max(0.0,raw)/max(1,lineage_counts[LINEAGE[e]])
    if weighted and max(weighted.values())>0:return sorted(weighted.items(),key=lambda x:(-x[1],str(x[0])))[0][0]
    return best_fallback[1] if best_fallback else None
def _stats(rows,preds):
    acc=sum(p==r.case.gold for p,r in zip(preds,rows))/len(rows);has=sum(any(v==r.case.gold for v in r.answers.values()) for r in rows);neg=sum(any(v==r.case.gold for v in r.answers.values()) and p!=r.case.gold for p,r in zip(preds,rows))/max(has,1);return {'accuracy':acc,'negative_transfer_rate':neg}
def evaluate_strategies(rows,model):
    singles={e:sum(r.answers[e]==r.case.gold for r in rows)/len(rows) for e in EXPERTS};be=max(singles,key=singles.get);best={'expert':be,'accuracy':singles[be]};allp=[_fuse(r,list(range(len(EXPERTS)))) for r in rows];heur=[]
    for r in rows:
        f=r.case.router_features()
        if f['support_count']>0 and f['cyrillic_ratio']>.05:sel=[1,0,5]
        elif f['support_count']>0:sel=[0,1,4]
        elif f['evidence_count']>0:sel=[6,4,3]
        elif f['option_count']>0:sel=[4,3,6]
        elif f['cyrillic_ratio']>.2:sel=[2,5,1]
        else:sel=[5,2,1]
        heur.append(_fuse(r,sel))
    sel,scores=route_with_scores(model,rows,3);learn=[learned_fuse(r,s,sc) for r,s,sc in zip(rows,sel,scores)];oracle=[r.case.gold if any(v==r.case.gold for v in r.answers.values()) else None for r in rows]
    out={'best_single':best,'naive_all':_stats(rows,allp),'heuristic_topk':_stats(rows,heur),'learned_moe':_stats(rows,learn),'oracle':_stats(rows,oracle),'per_expert':singles};per_family={}
    for fam in sorted({r.case.family for r in rows}):
        idx=[i for i,r in enumerate(rows) if r.case.family==fam];sub=[rows[i] for i in idx];fs={e:sum(r.answers[e]==r.case.gold for r in sub)/len(sub) for e in EXPERTS};fb=max(fs,key=fs.get)
        per_family[fam]={'best_single':{'expert':fb,'accuracy':fs[fb]},'naive_all':_stats(sub,[allp[i] for i in idx]),'heuristic_topk':_stats(sub,[heur[i] for i in idx]),'learned_moe':_stats(sub,[learn[i] for i in idx]),'oracle':_stats(sub,[oracle[i] for i in idx]),'per_expert':fs}
    out['per_family']=per_family;return out
