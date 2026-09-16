from __future__ import annotations
from collections import defaultdict, deque
from pathlib import Path
import joblib

FUNCTIONAL={'owned_by','located_in'}
TRANSITIVE={'before','is_a'}

class UnifiedNexusRuntime:
    def __init__(self, checkpoint_dir: str|Path|None=None):
        self.claims=defaultdict(list)
        self.edges=defaultdict(lambda:defaultdict(list))
        self.semantic=None; self.argument=None; self.context=None
        if checkpoint_dir is not None:
            p=Path(checkpoint_dir)
            self.semantic=joblib.load(p/'omega14r_semantic_operator.joblib')
            self.argument=joblib.load(p/'omega15r_joint_argument.joblib')
            self.context=joblib.load(p/'context_revision_binder_r.joblib')

    def upsert(self,relation,subject,obj,*,trust:float=1.0,source:str='unknown',revision:bool=False):
        trust=float(trust)
        if revision and relation in FUNCTIONAL:
            self.claims[(relation,subject)]=[]
        rec={'object':obj,'trust':trust,'source':source}
        if relation in TRANSITIVE:
            bucket=self.edges[relation][subject]
            if not any(x['object']==obj and x['source']==source for x in bucket): bucket.append(rec)
        else:
            self.claims[(relation,subject)].append(rec)
        return rec

    def retract(self,relation,subject,obj=None,*,source:str|None=None):
        if relation in TRANSITIVE:
            bucket=self.edges[relation][subject]
            self.edges[relation][subject]=[x for x in bucket if not ((obj is None or x['object']==obj) and (source is None or x['source']==source))]
        else:
            bucket=self.claims[(relation,subject)]
            self.claims[(relation,subject)]=[x for x in bucket if not ((obj is None or x['object']==obj) and (source is None or x['source']==source))]

    def _query_functional(self,relation,subject):
        rows=self.claims.get((relation,subject),[])
        if not rows:return {'object':None,'status':'unknown','depth':0,'evidence':[]}
        by={}
        for r in rows:
            by[r['object']]=max(by.get(r['object'],0.0),r['trust'])
        ranked=sorted(by.items(),key=lambda kv:(-kv[1],kv[0]))
        top_obj,top=ranked[0]
        if top < .60:return {'object':None,'status':'insufficient','depth':0,'evidence':rows}
        if len(ranked)>1 and ranked[1][1]>=.80 and top-ranked[1][1] < .05:
            return {'object':None,'status':'contested','depth':0,'evidence':rows}
        return {'object':top_obj,'status':'accepted','depth':1,'evidence':rows}

    def _query_transitive(self,relation,subject):
        q=deque([(subject,0)]); seen={subject:0}; best=[]
        while q:
            cur,d=q.popleft()
            for rec in self.edges[relation].get(cur,[]):
                nxt=rec['object']; nd=d+1
                if nd>seen.get(nxt,-1):
                    seen[nxt]=nd; q.append((nxt,nd)); best.append((nd,nxt))
        if not best:return {'object':None,'status':'unknown','depth':0,'evidence':[]}
        depth=max(d for d,_ in best); obj=sorted(x for d,x in best if d==depth)[0]
        return {'object':obj,'status':'accepted' if depth==1 else 'inferred','depth':depth,'evidence':[]}

    def query(self,subject,relation):
        if relation in TRANSITIVE:return self._query_transitive(relation,subject)
        return self._query_functional(relation,subject)

    def parse_ru(self,text:str):
        if self.semantic is None or self.argument is None: raise RuntimeError('checkpoint_dir is required for parse_ru')
        relation=self.semantic.predict([text])[0]
        if relation=='abstain': return {'relation':'abstain','subject':None,'object':None,'subject_span':None,'object_span':None}
        args=self.argument.predict_one(text,relation)
        return {'relation':relation,**args}

    def route_context(self,text:str):
        if self.context is None: raise RuntimeError('checkpoint_dir is required for route_context')
        return self.context.predict([text])[0]
