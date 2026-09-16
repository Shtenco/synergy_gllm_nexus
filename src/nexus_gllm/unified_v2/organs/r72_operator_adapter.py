from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

import torch
import torch.nn as nn

from nexus_gllm.unified_v2.organs.donor_adapters import ArtifactUnavailable

D = 192
N = 4096
STATE = ['янтарь', 'лазурь', 'графит', 'нефрит']
EFFECT = ['север', 'восток', 'юг', 'запад']
ACTION = ['мост', 'маяк', 'контур', 'шлюз']


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class _R7Core(nn.Module):
    def __init__(self, d=D, steps=3):
        super().__init__(); self.d=d; self.steps=steps
        self.demo=nn.Sequential(nn.Linear(12,d),nn.GELU(),nn.Linear(d,d),nn.LayerNorm(d))
        self.query=nn.Sequential(nn.Linear(6,d),nn.GELU(),nn.Linear(d,d),nn.LayerNorm(d))
        self.sk=nn.Linear(d,d,bias=False); self.sv=nn.Linear(d,d,bias=False); self.hq=nn.Linear(d,d,bias=False)
        self.msg=nn.Sequential(nn.Linear(2*d,2*d),nn.GELU(),nn.Linear(2*d,d)); self.g=nn.Linear(2*d,d); self.ln=nn.LayerNorm(d)
        self.eh=nn.Linear(d,4); self.ah=nn.Linear(d,4); self.halt=nn.Linear(d,1); self.ie=nn.Embedding(2,d)

    def forward(self, sraw, query):
        s=self.demo(sraw); h=self.query(query)+self.ie(query[:,4:].argmax(-1)); states=[]; ps=[]
        for _ in range(self.steps):
            att=(self.hq(h)[:,None]@self.sk(s).transpose(-1,-2)/math.sqrt(self.d)).softmax(-1)
            mem=(att@self.sv(s)).squeeze(1); cand=self.msg(torch.cat([h,mem],-1))
            gate=.08+.22*torch.sigmoid(self.g(torch.cat([h,mem],-1))); h=self.ln((1-gate)*h+gate*cand)
            states.append(h); ps.append(torch.sigmoid(self.halt(h)).squeeze(-1))
        rem=torch.ones(h.shape[0]); ws=[]
        for k,p in enumerate(ps):
            w=rem if k==len(ps)-1 else rem*p; ws.append(w); rem=rem*(1-p)
        weights=torch.stack(ws,1); weights=weights/(weights.sum(1,keepdim=True)+1e-9)
        z=sum(states[k]*weights[:,k,None] for k in range(len(states)))
        return self.eh(z), self.ah(z)


def _grams(text: str):
    text='^'+text.lower()+'$'; out=[]
    for n in (3,4,5):
        for i in range(len(text)-n+1):
            out.append(int(hashlib.blake2b(text[i:i+n].encode(),digest_size=8).hexdigest(),16)%N)
    return out or [0]


def _bag(xs):
    flat=[]; offsets=[]; c=0
    for x in xs:
        offsets.append(c); z=_grams(x); flat+=z; c+=len(z)
    return torch.tensor(flat), torch.tensor(offsets)


class _SpanClassifier(nn.Module):
    def __init__(self, out):
        super().__init__(); self.e=nn.EmbeddingBag(N,48,mode='mean'); self.m=nn.Sequential(nn.Linear(48,96),nn.GELU(),nn.Linear(96,out))
    def forward(self, xs):
        x,o=_bag(xs); return self.m(self.e(x,o))


def _spans(text: str):
    return re.findall(r'«([^»]+)»', text)


def _contentless(text: str):
    return re.sub(r'«[^»]+»', ' ', text)


class R72OperatorAdapter:
    organ_id = 'russian_binder_unseen_operator'
    source_version = 'R7.2'

    def __init__(self, root: Path):
        root=Path(root); core_path=root/'r7l_core_seed712.pt'; binder_path=root/'r72_language_binder.pt'
        if not core_path.is_file() or not binder_path.is_file():
            raise ArtifactUnavailable(f'missing R7.2 checkpoint(s) under {root}')
        self.core_sha256=_sha256(core_path); self.binder_sha256=_sha256(binder_path)
        try:
            self.core=_R7Core(); state=torch.load(core_path,map_location='cpu',weights_only=False)
            self.core.load_state_dict(state if isinstance(state,dict) and 'demo.0.weight' in state else state.get('state_dict',state)); self.core.eval()
            self.state=_SpanClassifier(4); self.effect=_SpanClassifier(4); self.action=_SpanClassifier(4); self.intent=_SpanClassifier(2)
            binder=torch.load(binder_path,map_location='cpu',weights_only=False)
            self.state.load_state_dict(binder['state']); self.effect.load_state_dict(binder['effect']); self.action.load_state_dict(binder['action']); self.intent.load_state_dict(binder['intent'])
            for model in (self.state,self.effect,self.action,self.intent): model.eval()
        except Exception as exc:
            raise ArtifactUnavailable(f'cannot load R7.2 artifacts: {exc}') from exc

    def _parse_support(self, texts):
        ss=[]; ee=[]; aa=[]
        for text in texts:
            quoted=_spans(text)
            if len(quoted)<3: raise ValueError('R7.2 support requires three quoted symbols')
            ss.append(quoted[0]); ee.append(quoted[1]); aa.append(quoted[2])
        ps=self.state(ss).argmax(-1); pe=self.effect(ee).argmax(-1); pa=self.action(aa).argmax(-1)
        mat=torch.zeros(len(texts),12); mat[range(len(texts)),ps]=1; mat[range(len(texts)),4+pe]=1; mat[range(len(texts)),8+pa]=1
        return mat

    def _parse_query(self, texts):
        quoted=[_spans(t) for t in texts]
        if any(not q for q in quoted): raise ValueError('R7.2 query requires a quoted state symbol')
        ss=[q[0] for q in quoted]; qst=self.state(ss).argmax(-1); intent=self.intent([_contentless(t) for t in texts]).argmax(-1)
        q=torch.zeros(len(texts),6); q[range(len(texts)),qst]=1; q[range(len(texts)),4+intent]=1
        return q,intent

    def solve_case(self, case: dict) -> str:
        support=case['support']; query=case['query']
        with torch.no_grad():
            smat=self._parse_support(support).view(1,len(support),12); q,intent=self._parse_query([query]); effect_logits,action_logits=self.core(smat,q)
            which=int(intent[0]); idx=int((effect_logits if which==0 else action_logits).argmax(-1))
        return (EFFECT if which==0 else ACTION)[idx]
