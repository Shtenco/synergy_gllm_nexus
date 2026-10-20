#!/usr/bin/env python3
# NEXUS-OMEGA V28: fast word n-gram decoder + learned ternary reranker.
# Research-only standalone; does NOT import or overwrite previous V27 weights.
# Corpus: OpenCorpora CC-BY-SA 3.0. Python 3.10+; stdlib only.
from __future__ import annotations
import argparse, base64, collections, gzip, hashlib, json, math, os, random
import re, statistics, time, urllib.request, xml.etree.ElementTree as ET
import zlib
from pathlib import Path

PAT = re.compile(r"[а-яё]+(?:-[а-яё]+)*|[a-z]+|\d+|[.,!?;:()«»—-]", re.I)
W = 32768
ORDER = 5
LINK = "https://raw.githubusercontent.com/alesapin/XMorphy/master/data/corpuses/opencorpora/annot.opcorpora.no_ambig.xml"
SOURCE = "OpenCorpora / XMorphy; CC BY-SA 3.0"

def words(s):
    return PAT.findall(str(s).lower())

def untokenize(toks):
    s = ""
    for w in toks:
        if not s or w in ",.!?;:»)" or s.endswith(("«", "(", "—")):
            s += w
        elif w == "«":
            s += " " + w
        elif w == "—":
            s += " — "
        else:
            s += " " + w
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s[:1].upper() + s[1:] if s else s

def parse_documents(path, limit=0):
    path=Path(path)
    if path.suffix == ".xml":
        docs=[]
        for _, e in ET.iterparse(str(path), events=("end",)):
            if e.tag.split("}")[-1] != "text": continue
            ss=[]
            for se in e.iter():
                if se.tag.split("}")[-1]!="sentence": continue
                tt=[]
                for tok in se.iter():
                    if tok.tag.split("}")[-1]=="token":
                        word=tok.attrib.get("text","")
                        if word: tt.append(word)
                if 4 <= len(tt) <= 90:
                    ss.append(untokenize(tt))
            if ss: docs.append(ss)
            e.clear()
            if limit and len(docs)>=limit: break
        if not docs: raise ValueError("XML contains no <text>/<sentence>/<token> structures")
        return docs
    docs=[]
    raw = path.read_text("utf-8", errors="replace")
    for p in re.split(r"\n\s*\n", raw):
        ss=[x.strip() for x in re.split(r"(?<=[.!?])\s+",p.replace("\n"," ")) if 5 <= len(words(x)) <= 90]
        if ss: docs.append(ss)
        if limit and len(docs)>=limit:break
    if not docs: raise ValueError("Corpus has no parseable Russian sentences")
    return docs

def split_docs(docs):
    # Hold out WHOLE DOCUMENTS, never individual overlapping sentences.
    sets={"train":[],"val":[],"test":[]}
    for d in docs:
        key="\n".join(d[:6]).encode("utf-8")
        h=int(hashlib.sha256(key).hexdigest()[:8],16)%100
        sets["train" if h<85 else "val" if h<93 else "test"].append(d)
    return sets

def download_source(dest):
    u=urllib.request.Request(LINK,headers={"User-Agent":"NEXUS-V28-Research/1.0"})
    with urllib.request.urlopen(u,timeout=50) as f,open(dest,"wb") as o:
        while True:
            b=f.read(65536)
            if not b: break
            o.write(b)
    if Path(dest).stat().st_size < 10000:
        raise RuntimeError("Downloaded source unexpectedly small")

class Decoder:
    def __init__(self, n=ORDER, w=W):
        self.n=n; self.w=w
        self.tbl=[collections.defaultdict(collections.Counter) for _ in range(n)]
        self.total=0
        self.weight=bytearray([1])*w  # packed values 0=>-1,1=>0,2=>+1
        self.momentum=bytearray([8])*w  # unsigned encoding [-8,8]
        self.unigram_total=1
    def observe(self, sent):
        seq=["<s>"]*(self.n-1)+words(sent)+["</s>"]
        if len(seq) < self.n+2:return
        for i in range(self.n-1,len(seq)):
            for k in range(self.n):
                ctx=tuple(seq[max(0,i-k):i]) if k else ()
                self.tbl[k][ctx][seq[i]]+=1
            self.total+=1
    def fit_counts(self, docs, max_sentences=0):
        seen=0
        for d in docs:
            for sent in d:
                self.observe(sent); seen+=1
                if max_sentences and seen>=max_sentences: break
            if max_sentences and seen>=max_sentences:break
        self.unigram_total=sum(self.tbl[0][()].values())
        return seen
    def candidates(self, context, topk=24):
        counts=collections.Counter()
        for k in range(self.n-1,-1,-1):
            key=tuple(context[-k:]) if k else ()
            row=self.tbl[k].get(key)
            if row:
                # Sparse lookups; never project full vocabulary.
                for tok,c in row.most_common(topk):
                    counts[tok]+=c*(2**k)
            if len(counts)>=topk*2:break
        if not counts: return []
        return [w for w,_ in counts.most_common(topk)]
    def logprob(self, context, tok):
        # Interpolated discounted conditionals; conservative unknown floor.
        ps=[]; ww=[]
        for k in range(self.n-1,-1,-1):
            key=tuple(context[-k:]) if k else ()
            row=self.tbl[k].get(key)
            if row:
                tot=sum(row.values())
                v=row.get(tok,0)
                if v:
                    ps.append(v/(tot+len(row)*0.15))
                    ww.append(1.0+1.5*k)
        if not ps:return -16.0
        p=sum(a*b for a,b in zip(ps,ww))/sum(ww)
        return math.log(max(p,1e-12))
    def feats(self, context, tok):
        # Deterministic sparse hashed conjunctions. Ternary weights only.
        c=tuple(context[-4:])
        keys=["t="+tok,"last="+(c[-1] if c else "")+"|"+tok,
              "end="+(c[-1][-2:] if c else "")+"|"+tok[-2:],
              "pair="+(" ".join(c[-2:]))+"|"+tok,
              "triple="+(" ".join(c[-3:]))+"|"+tok,
              "pref="+tok[:3]+"|"+(c[-1][-3:] if c else ""),
              "suff="+tok[-3:]+"|"+(c[-1][-3:] if c else ""),
              "len="+str(min(len(tok),12))+"|"+(c[-1] if c else "")]
        return [zlib.crc32(k.encode("utf-8"))%self.w for k in keys]
    def ternary_score(self,ctx,tok):
        return sum(self.weight[j]-1 for j in self.feats(ctx,tok))
    def choose(self,context,topk=24,alpha=0.22,use_ternary=True):
        candidates=self.candidates(context,topk)
        if not candidates:return "</s>"
        best=None; bestv=-1e30
        for tok in candidates:
            score=self.logprob(context,tok)
            if use_ternary:score+=alpha*self.ternary_score(context,tok)
            if score>bestv:
                bestv=score;best=tok
        return best
    def step_ternary(self,positive,negative):
        for j in positive:
            m=min(16,self.momentum[j]+1)
            self.momentum[j]=m
            if m>=12:self.weight[j]=2
        for j in negative:
            m=max(0,self.momentum[j]-1)
            self.momentum[j]=m
            if m<=4:self.weight[j]=0
        # Decay dead accumulators towards neutral (cheap, only active features)
    def fit_ranker(self, docs, epochs=3,max_positions=90000,alpha=0.22,seed=77):
        # Train only on held-out TRAIN documents, no validation/test in update.
        rng=random.Random(seed)
        seqs=[]
        for d in docs:
            for sent in d:
                seq=["<s>"]*(self.n-1)+words(sent)+["</s>"]
                if len(seq)>=self.n+2:seqs.append(seq)
        rng.shuffle(seqs)
        updates=seen=eligible=0
        for epoch in range(epochs):
            rng.shuffle(seqs)
            for seq in seqs:
                for i in range(self.n-1,len(seq)):
                    ctx=seq[max(0,i-self.n+1):i]
                    gold=seq[i]
                    seen+=1
                    cand=self.candidates(ctx)
                    if gold not in cand or len(cand)<2: continue
                    eligible+=1
                    guess=self.choose(ctx,alpha=alpha)
                    if guess!=gold:
                        self.step_ternary(self.feats(ctx,gold),self.feats(ctx,guess))
                        updates+=1
                    if seen>=max_positions*(epoch+1): break
                if seen>=max_positions*(epoch+1):break
        return dict(exposures=seen,eligible=eligible,updates=updates,
                    ternary_nonzero=sum(1 for x in self.weight if x!=1),
                    total_weights=self.w,epochs=epochs)
    def evaluate(self, docs,max_positions=12000,alpha=0.22):
        ok0=ok1=n=candidate_hit=0
        start=time.perf_counter()
        for d in docs:
            for s in d:
                seq=["<s>"]*(self.n-1)+words(s)+["</s>"]
                for i in range(self.n-1,len(seq)):
                    ctx=seq[max(0,i-self.n+1):i]; gold=seq[i]
                    cand=self.candidates(ctx)
                    if gold in cand: candidate_hit+=1
                    ok0+=self.choose(ctx,use_ternary=False)==gold
                    ok1+=self.choose(ctx,use_ternary=True,alpha=alpha)==gold
                    n+=1
                    if n>=max_positions: break
                if n>=max_positions: break
            if n>=max_positions:break
        elapsed=time.perf_counter()-start
        return dict(tokens=n,ngram_top1=ok0/max(n,1),hybrid_top1=ok1/max(n,1),
                    candidate_recall=candidate_hit/max(n,1),eval_toks_per_sec=n/max(elapsed,1e-6))
    def generate(self,prompt,max_tokens=70,alpha=0.22,seed=7):
        # Greedy decodes as benchmark; full text is not guaranteed factual.
        ctx=["<s>"]*(self.n-1)+words(prompt)
        out=[]
        for _ in range(max_tokens):
            t=self.choose(ctx,alpha=alpha)
            if t in ("</s>","<s>"):break
            out.append(t);ctx.append(t)
            if t in (".","!","?") and len(out)>=12:break
        return untokenize(out)
    def bench(self,tries=400):
        ctx=["<s>"]*(self.n-1)+words("Язык и морфология помогают понимать структуру предложения")
        start=time.perf_counter()
        for i in range(tries):
            tok=self.choose(ctx);ctx.append(tok)
            if tok=="</s>":ctx=["<s>"]*(self.n-1)+words("Мы исследуем русский язык")
        sec=time.perf_counter()-start
        return dict(decisions=tries,seconds=sec,decisions_per_second=tries/max(sec,1e-6),
                    implementation="Python 3 stdlib; no SIMD; not normalized to V27 hardware")
    def save(self,path):
        packed=bytearray((self.w+3)//4)
        for i,v in enumerate(self.weight):
            packed[i//4]|=(v&3)<<((i%4)*2)
        tables=[]
        for t in self.tbl:
            tables.append([["\t".join(k),list(c.items())] for k,c in t.items()])
        state={"version":"V28-experimental","order":self.n,"w":self.w,
               "weights_2bit_base64":base64.b64encode(packed).decode(),
               "tables":tables,"token_exposures":self.total,"source":SOURCE}
        with gzip.open(path,"wt",encoding="utf-8",compresslevel=6) as f:json.dump(state,f,ensure_ascii=False,separators=(",",":"))
    @classmethod
    def load(cls,path):
        with gzip.open(path,"rt",encoding="utf-8") as f:v=json.load(f)
        obj=cls(v["order"],v["w"])
        raw=base64.b64decode(v["weights_2bit_base64"])
        for i in range(obj.w):obj.weight[i]=(raw[i//4]>>((i%4)*2))&3
        obj.tbl=[collections.defaultdict(collections.Counter) for _ in range(obj.n)]
        for t,items in zip(obj.tbl,v["tables"]):
            for k,c in items:
                key=tuple(k.split("\t")) if k else ()
                t[key]=collections.Counter(dict(c))
        obj.total=v["token_exposures"]
        return obj

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--corpus",default="data/annot.opcorpora.no_ambig.xml")
    p.add_argument("--download",action="store_true")
    p.add_argument("--output",default="artifacts/v28_decoder.json.gz")
    p.add_argument("--max-docs",type=int,default=0)
    p.add_argument("--max-sentences",type=int,default=0)
    p.add_argument("--positions",type=int,default=40000)
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--mode",choices=("train","eval","generate","selftest"),default="train")
    p.add_argument("--prompt",default="Русский язык и морфология")
    a=p.parse_args()
    if a.mode=="selftest":
        x=Decoder();x.observe("Новая система анализирует русский текст.")
        x.weight[:4]=bytes([0,1,2,1])
        x.save("/tmp/nexus_v28_selftest.gz")
        y=Decoder.load("/tmp/nexus_v28_selftest.gz")
        assert list(y.weight[:4])==[0,1,2,1]
        assert x.candidates(["<s>"]*4)==y.candidates(["<s>"]*4)
        assert y.generate("Новая система")
        print(json.dumps({"selftest":"PASS"},ensure_ascii=False))
        return
    if a.mode=="generate":
        m=Decoder.load(a.output)
        print(json.dumps({"prompt":a.prompt,"generation":m.generate(a.prompt),"speed":m.bench()},ensure_ascii=False,indent=2))
        return
    if a.download and not Path(a.corpus).exists():
        Path(a.corpus).parent.mkdir(parents=True,exist_ok=True)
        download_source(a.corpus)
    docs=parse_documents(a.corpus,a.max_docs)
    parts=split_docs(docs)
    if len(parts["train"])<2 or not parts["test"]:
        raise RuntimeError("Not enough distinct documents for train and test")
    m=Decoder()
    ntrain=m.fit_counts(parts["train"],a.max_sentences)
    out={"source":SOURCE,"document_split":{k:len(v) for k,v in parts.items()},
         "train_sentences":ntrain}
    if a.mode=="train":
        out["training"]=m.fit_ranker(parts["train"],a.epochs,a.positions)
        Path(a.output).parent.mkdir(parents=True,exist_ok=True)
        m.save(a.output)
        m=Decoder.load(a.output) # roundtrip test
    else:
        m=Decoder.load(a.output)
    if parts["val"]:out["validation"]=m.evaluate(parts["val"],max_positions=5000)
    out["test"]=m.evaluate(parts["test"],max_positions=10000)
    out["speed"]=m.bench(400)
    out["generation_samples"]={x:m.generate(x) for x in [
        "Русский язык состоит из", "Учёные исследуют", "Морфология помогает"]}
    out["research_limits"]="Corpus dependent; data not user V27 checkpoint; small standalone ternary reranker, not semantic LLM"
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/report.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),"utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
