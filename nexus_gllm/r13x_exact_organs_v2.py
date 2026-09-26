from __future__ import annotations
import hashlib, importlib.util, json, pickle, re, sys
from pathlib import Path
from typing import Any

class ExactOrganV2:
    def __init__(self, root: str | Path):
        self.root=Path(root)
        self.loaded={}
        self.errors={}
        self._load_all()

    def _find_dir(self, key:str):
        base=self.root/key
        if not base.exists(): return None
        dirs=[p for p in base.iterdir() if p.is_dir()]
        return dirs[0] if dirs else None

    def _load_all(self):
        # R7.6 semantic memory
        try:
            d=self._find_dir("r76")
            p=(d/"r76_semantic_knowledge_organ.pkl") if d else None
            if p and p.is_file():
                obj=pickle.load(open(p,"rb"))
                self.loaded["r76"]={"obj":obj,"root":d}
        except Exception as e: self.errors["r76"]=f"{type(e).__name__}: {e}"

        # R7.8 native authority
        try:
            d=self._find_dir("r78")
            p=(d/"02_NATIVE_AUTHORITY_FROZEN.py") if d else None
            if p and p.is_file():
                spec=importlib.util.spec_from_file_location("nexus_r78_v2",str(p))
                m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
                self.loaded["r78"]={"mod":m,"root":d}
        except Exception as e: self.errors["r78"]=f"{type(e).__name__}: {e}"

        # R7.10 proof-first
        try:
            d=self._find_dir("r710")
            src=(d/"FREEZE/source") if d else None
            if src and (src/"runtime_v2.py").is_file():
                if str(src) not in sys.path: sys.path.insert(0,str(src))
                import runtime_v2
                self.loaded["r710"]={"mod":runtime_v2,"root":d,"src":src}
        except Exception as e: self.errors["r710"]=f"{type(e).__name__}: {e}"

        # R7.14 MorphoLex
        try:
            d=self._find_dir("r714")
            src=(d/"source") if d else None
            if src and (src/"morpholex_engine.py").is_file():
                if str(src) not in sys.path: sys.path.insert(0,str(src))
                import morpholex_engine
                self.loaded["r714"]={"mod":morpholex_engine,"root":d,"src":src}
        except Exception as e: self.errors["r714"]=f"{type(e).__name__}: {e}"

    def status(self):
        return {"loaded":sorted(self.loaded),"errors":dict(self.errors)}

    def canonicalize(self,text:str):
        o=self.loaded.get("r714")
        if not o:return {"language":None,"canonical":text,"used":False}
        lang,_=o["mod"].detect_language(text)
        return {"language":lang,"canonical":o["mod"].canonicalize(text),"used":True}

    def semantic_answer(self,text:str,min_similarity:float=.42):
        o=self.loaded.get("r76")
        if not o:return None
        obj=o["obj"]; X=obj["vectorizer"].transform([text])
        questions=[a.get("question","") for a in obj["atoms"]]
        Q=obj["vectorizer"].transform(questions)
        sims=(X@Q.T).toarray()[0]
        idx=int(sims.argmax()) if len(sims) else 0
        max_sim=float(sims[idx]) if len(sims) else 0.0
        if max_sim < min_similarity:return None
        pred=[m.predict(X)[0] for m in obj["models"]]
        best=max(set(pred),key=lambda x:(pred.count(x),x))
        byid={a["id"]:a for a in obj["atoms"]}
        atom=byid.get(best)
        if not atom:return None
        return {
            "answer": atom.get("semantic_answer"),
            "atom_id": best,
            "votes": pred,
            "domain": atom.get("domain"),
            "similarity": max_sim,
            "nearest_question": questions[idx],
            "governor_correct": atom.get("governor_correct"),
            "governor_letter": atom.get("governor_letter"),
            "gold_letter": atom.get("gold_letter"),
            "trust_top_probability": atom.get("trust_top_probability"),
            "trust_margin": atom.get("trust_margin"),
        }

    def proof(self,question:str):
        o=self.loaded.get("r710")
        if not o:return None
        m=o["mod"]
        try:
            item={"q":question,"options":{}}
            ir=m.compile_item(item)
            if ir is None:return None
            proof=m.solve(ir); ver=m.verify(ir,proof)
            return {
                "status":ver.status,
                "conclusion":proof.conclusion if proof else None,
                "ir":m.dump_obj(ir),
                "proof":m.dump_obj(proof) if proof else None,
                "verification":m.dump_obj(ver),
            }
        except Exception:return None

    def solve_mcq(self,question:str,options:dict[str,str]):
        out={}
        if "r78" in self.loaded:
            try:
                ans,rule=self.loaded["r78"]["mod"].solve({"q":question,"options":options})
                out["r78"]={"answer":ans,"rule":rule}
            except Exception: out["r78"]=None
        if "r710" in self.loaded:
            try: out["r710"]=self.loaded["r710"]["mod"].formal_pass({"q":question,"options":options})
            except Exception: out["r710"]=None
        return out
