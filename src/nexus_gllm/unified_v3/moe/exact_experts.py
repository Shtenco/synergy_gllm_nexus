from __future__ import annotations
from pathlib import Path
import hashlib, importlib.util, math, pickle, random, re, sys
import torch
from torch import nn

class _R7(nn.Module):
    def __init__(self,d=192,steps=3):
        super().__init__();self.d=d;self.steps=steps
        self.demo=nn.Sequential(nn.Linear(12,d),nn.GELU(),nn.Linear(d,d),nn.LayerNorm(d));self.query=nn.Sequential(nn.Linear(6,d),nn.GELU(),nn.Linear(d,d),nn.LayerNorm(d));self.sk=nn.Linear(d,d,bias=False);self.sv=nn.Linear(d,d,bias=False);self.hq=nn.Linear(d,d,bias=False);self.msg=nn.Sequential(nn.Linear(2*d,2*d),nn.GELU(),nn.Linear(2*d,d));self.g=nn.Linear(2*d,d);self.ln=nn.LayerNorm(d);self.eh=nn.Linear(d,4);self.ah=nn.Linear(d,4);self.halt=nn.Linear(d,1);self.ie=nn.Embedding(2,d)
    def forward(self,Sraw,Q):
        S=self.demo(Sraw);h=self.query(Q)+self.ie(Q[:,4:].argmax(-1));states=[];ps=[]
        for _ in range(self.steps):
            att=(self.hq(h)[:,None]@self.sk(S).transpose(-1,-2)/math.sqrt(self.d)).softmax(-1);mem=(att@self.sv(S)).squeeze(1);cand=self.msg(torch.cat([h,mem],-1));g=.08+.22*torch.sigmoid(self.g(torch.cat([h,mem],-1)));h=self.ln((1-g)*h+g*cand);states.append(h);ps.append(torch.sigmoid(self.halt(h)).squeeze(-1))
        rem=torch.ones(h.shape[0]);ws=[]
        for k,p in enumerate(ps):w=rem if k==len(ps)-1 else rem*p;ws.append(w);rem=rem*(1-p)
        W=torch.stack(ws,1);W=W/(W.sum(1,keepdim=True)+1e-9);z=sum(states[k]*W[:,k,None] for k in range(len(states)))
        return self.eh(z),self.ah(z)

class R7LExactExpert:
    def __init__(self,checkpoint):
        self.model=_R7();self.model.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True));self.model.eval()
    def predict(self,support,query_state,intent):
        S=torch.zeros(1,3,12);Q=torch.zeros(1,6)
        for j,(s,e,a) in enumerate(support):S[0,j,s]=1;S[0,j,4+e]=1;S[0,j,8+a]=1
        it=0 if intent in ('effect',0) else 1;Q[0,query_state]=1;Q[0,4+it]=1
        with torch.no_grad():el,al=self.model(S,Q);return int((el if it==0 else al).argmax(-1))

class R7LCollectiveExactExpert:
    def __init__(self,checkpoints):
        self.models=[]
        for checkpoint in checkpoints:
            m=_R7();m.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True));m.eval();self.models.append(m)
        if len(self.models)!=3: raise ValueError('R7-L collective requires exactly three frozen checkpoints')
    def predict(self,support,query_state,intent):
        S=torch.zeros(1,3,12);Q=torch.zeros(1,6)
        for j,(s,e,a) in enumerate(support):S[0,j,s]=1;S[0,j,4+e]=1;S[0,j,8+a]=1
        it=0 if intent in ('effect',0) else 1;Q[0,query_state]=1;Q[0,4+it]=1
        with torch.no_grad():
            logits=[]
            for m in self.models:
                el,al=m(S,Q);logits.append(el if it==0 else al)
            return int(torch.stack(logits).mean(0).argmax(-1))

N=4096
class _SpanClassifier(nn.Module):
    def __init__(self,out):super().__init__();self.e=nn.EmbeddingBag(N,48,mode='mean');self.m=nn.Sequential(nn.Linear(48,96),nn.GELU(),nn.Linear(96,out))
    @staticmethod
    def _grams(t):
        t='^'+t.lower()+'$';a=[]
        for n in (3,4,5):
            for i in range(len(t)-n+1):a.append(int(hashlib.blake2b(t[i:i+n].encode(),digest_size=8).hexdigest(),16)%N)
        return a or [0]
    def forward(self,xs):
        flat=[];off=[];c=0
        for x in xs:off.append(c);z=self._grams(x);flat+=z;c+=len(z)
        return self.m(self.e(torch.tensor(flat),torch.tensor(off)))

class R72ExactExpert:
    STATE=['янтарь','лазурь','графит','нефрит']; EFFECT=['север','восток','юг','запад']; ACTION=['мост','маяк','контур','шлюз']
    def __init__(self,binder,core):
        ck=torch.load(binder,map_location='cpu',weights_only=True)
        self.state=_SpanClassifier(4);self.effect=_SpanClassifier(4);self.action=_SpanClassifier(4);self.intent=_SpanClassifier(2)
        for k,m in [('state',self.state),('effect',self.effect),('action',self.action),('intent',self.intent)]:m.load_state_dict(ck[k]);m.eval()
        self.core=_R7();self.core.load_state_dict(torch.load(core,map_location='cpu',weights_only=True));self.core.eval()
    @staticmethod
    def _spans(t):return re.findall(r'«([^»]+)»',t)
    def predict(self,support_texts,query):
        spans=[self._spans(t) for t in support_texts]; ss=[x[0] for x in spans];ee=[x[1] for x in spans];aa=[x[2] for x in spans]
        with torch.no_grad():ps=self.state(ss).argmax(-1);pe=self.effect(ee).argmax(-1);pa=self.action(aa).argmax(-1)
        S=torch.zeros(1,3,12)
        for j in range(3):S[0,j,ps[j]]=1;S[0,j,4+pe[j]]=1;S[0,j,8+pa[j]]=1
        qs=self._spans(query)[0]; clean=re.sub(r'«[^»]+»',' ',query)
        with torch.no_grad():qst=int(self.state([qs]).argmax(-1));it=int(self.intent([clean]).argmax(-1));Q=torch.zeros(1,6);Q[0,qst]=1;Q[0,4+it]=1;el,al=self.core(S,Q);pred=int((el if it==0 else al).argmax(-1))
        return (self.EFFECT if it==0 else self.ACTION)[pred]

class R76ExactExpert:
    def __init__(self,path):self.obj=pickle.load(open(path,'rb'));self.byid={a['id']:a for a in self.obj['atoms']}
    def answer(self,text):
        X=self.obj['vectorizer'].transform([text]);pred=[m.predict(X)[0] for m in self.obj['models']];best=max(set(pred),key=lambda x:(pred.count(x),x));return self.byid.get(best,{}).get('semantic_answer')

def _load_file(name,path):
    spec=importlib.util.spec_from_file_location(name,str(path));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class R78ExactExpert:
    def __init__(self,root=Path('/mnt/data/nexus_moe_artifacts/r78/NEXUS_R78_TOP2_ARBITRATION_REAL_BLIND25_2026-08-20')):self.mod=_load_file('nexus_r78_exact',Path(root)/'02_NATIVE_AUTHORITY_FROZEN.py')
    def answer(self,item):
        try:r=self.mod.solve(item);return r[0] if r else None
        except Exception:return None

class R710ExactExpert:
    def __init__(self,root=Path('/mnt/data/nexus_moe_artifacts/r710/NEXUS_R710_PROOF_FIRST_FREEZE_2026-08-21')):
        src=Path(root)/'source';sys.path.insert(0,str(src)) if str(src) not in sys.path else None;self.mod=__import__('runtime_v2')
    def answer(self,item):
        try:return self.mod.formal_pass(item)
        except Exception:return {'status':'UNSUPPORTED','answer':None}

class R714ExactExpert:
    def __init__(self,root=Path('/mnt/data/nexus_moe_artifacts/r714/NEXUS_R714_MULTILINGUAL_MORPHOLEX_FREEZE_2026-08-23')):
        src=Path(root)/'source';sys.path.insert(0,str(src)) if str(src) not in sys.path else None;self.mod=__import__('morpholex_engine')
    def analyze(self,text):lang,_=self.mod.detect_language(text);return lang,self.mod.canonicalize(text)

class R718ExactExpert:
    TEACHERS=['ministral3_3b','phi4mini_3_8b','granite33_2b','qwen3_1_7b','gemma3_1b']; LABELS='ABCD'
    def __init__(self,root=Path('/mnt/data/nexus_moe_artifacts/r718/NEXUS_R718_BEST_OF_EVIDENCE_CREDIT_FREEZE_2026-08-23')):
        src=Path(root)/'source';sys.path.insert(0,str(src)) if str(src) not in sys.path else None;self.mod=__import__('runtime_r718')
    def make_teacher_rows(self,gold,seed=0,noise=.15):
        r=random.Random(seed);rows={}
        for i,t in enumerate(self.TEACHERS):
            chosen=gold if r.random()>noise else r.choice([x for x in self.LABELS if x!=gold]);lp={a:-4.5 for a in self.LABELS};lp[chosen]=-0.05-r.random()*.1;rows[t]={'pred':chosen,'option_logprobs':lp}
        return rows
    def answer(self,item,rows=None):return self.mod.decide(item,rows or {})
