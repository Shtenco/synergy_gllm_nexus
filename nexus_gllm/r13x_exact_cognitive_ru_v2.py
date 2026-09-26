from __future__ import annotations
import re
from collections import deque
from pathlib import Path
from typing import Any

from .r13x_cognitive_ru import (
    CognitiveRussianRuntime, CognitiveRUResponse, ParsedRU, _norm, _cap, _stem_ru
)
from .r13x_exact_organs_v2 import ExactOrganV2

class ExactCognitiveRussianRuntimeV2(CognitiveRussianRuntime):
    """R1.3-X Cognitive Russian Runtime V2 with verified historical exact organs."""

    def __init__(self, memory_path: str|Path|None=None, artifact_root: str|Path|None=None):
        super().__init__(memory_path=memory_path, artifact_root=None)
        self.exact_v2 = ExactOrganV2(artifact_root) if artifact_root else None

    def exact_status(self):
        return self.exact_v2.status() if self.exact_v2 else {"loaded":[],"errors":{}}

    def _remember_focus(self,session_id:str,entity:str):
        if entity:
            self.memory.remember(session_id,"__focus_entity__",entity,source="system")

    def _focus(self,session_id:str):
        x=self.memory.recall(session_id,"__focus_entity__")
        return x["value"] if x else None

    def _causal_path(self,session_id:str,target:str,max_depth:int=6):
        edges=self.memory.causal_edges(session_id)
        target_n=_norm(target)
        def toks(x): return {_stem_ru(w) for w in re.findall(r"[а-яёa-z0-9]+",_norm(x)) if len(w)>=3}
        tt=toks(target_n)
        incoming={}
        for e in edges:
            incoming.setdefault(_norm(e["effect"]),[]).append(e)
        # Find any edge whose effect resembles target.
        starts=[e for e in edges if (_norm(e["effect"]) in target_n or target_n in _norm(e["effect"]) or toks(e["effect"]) & tt)]
        if not starts:return []
        best=starts[-1]; path=[best]
        seen={_norm(best["effect"])}
        cur=_norm(best["cause"])
        for _ in range(max_depth-1):
            prev=[e for e in edges if _norm(e["effect"])==cur or toks(e["effect"]) & toks(cur)]
            if not prev:break
            e=prev[-1]
            if _norm(e["effect"]) in seen:break
            path.append(e);seen.add(_norm(e["effect"]));cur=_norm(e["cause"])
        return list(reversed(path))

    def _render_causal_path(self,path):
        if not path:return None
        if len(path)==1:
            e=path[0]
            return f"По сохранённой причинной модели: {e['cause']} приводит к «{e['effect']}»."
        parts=[path[0]["cause"]]+[e["effect"] for e in path]
        return "Причинная цепочка: " + " → ".join(parts) + "."

    def _proof_answer(self,text:str):
        if not self.exact_v2:return None
        p=self.exact_v2.proof(text)
        if not p or p.get("status")!="VERIFIED" or p.get("conclusion") is None:return None
        c=p["conclusion"]
        return str(c),p

    @staticmethod
    def _parse_mcq(text:str):
        matches=list(re.finditer(r"\b([A-DА-Г])\)\s*([^\n]+?)(?=\s+\b[A-DА-Г]\)|$)",text,re.I))
        if len(matches)<2:return None
        options={m.group(1).upper():m.group(2).strip(" .;") for m in matches}
        q=text[:matches[0].start()].strip()
        q=re.sub(r"^(?:выбери|выберите|укажи|укажите)\s+(?:правильный\s+)?вариант[:.]?\s*","",q,flags=re.I)
        return q,options

    def answer(self,text:str,session_id:str="default")->CognitiveRUResponse:
        original=text
        mcq=self._parse_mcq(text)
        if mcq and self.exact_v2:
            q,options=mcq
            votes=self.exact_v2.solve_mcq(q,options)
            a78=(votes.get("r78") or {}).get("answer")
            r710=votes.get("r710") or {}
            a710=r710.get("answer") if r710.get("status")=="VERIFIED" else None
            agreed=a78 if a78 and a78==a710 else None
            p=ParsedRU("exact_mcq",{},.999,_norm(q))
            if agreed:
                val=options.get(agreed,"")
                return self._finish(session_id,p,f"Проверенный вариант: {agreed} — {val}.",evidence=("r78_exact_authority","r710_verified_proof"),organ="exact_consensus",trace=(f"r78={a78}",f"r710={a710}"))
            return self._finish(session_id,p,self.renderer.render("evidence_missing"),abstained=True,evidence=("exact_consensus_failed",),organ="exact_consensus",trace=(f"r78={a78}",f"r710={a710}"))
        original=text
        morph=None
        if self.exact_v2:
            try:
                morph=self.exact_v2.canonicalize(text)
            except Exception:
                morph=None

        # Handle simple anaphora over focused world entity.
        t=_norm(text)
        focus=self._focus(session_id)
        if focus:
            if re.search(r"(?:каков[оа]?|какой)\s+(?:его|её|ее)\s+(?:статус|состояние)",t):
                attr="состояние" if "состояни" in t else "статус"
                text=f"Каково {attr} {focus}?"
            elif re.search(r"^(?:каков|какой|каково|что|в каком)",t) and re.search(r"\b(?:его|её|ее|этого объекта|этой сущности)\b",t) and ("статус" in t or "состояни" in t):
                text=re.sub(r"\b(?:его|её|ее|этого объекта|этой сущности)\b",focus,text,flags=re.I)

        # Try base parser first.
        parsed=self.parser.parse(text)

        # On unknown, retry with MorphoLex canonical form if Russian.
        if parsed.intent=="unknown" and morph and morph.get("used") and morph.get("language")=="ru":
            cp=self.parser.parse(morph["canonical"])
            if cp.intent!="unknown":
                parsed=cp

        # Exact R7.10 proof-first for free-form exact/formal questions.
        if parsed.intent in ("arithmetic","formal_modus_ponens","formal_some") or any(
            k in _norm(text) for k in ("чему равно","вычисли","обязательно следует","логически","наибольший общий делитель","python","sql")
        ):
            proof=self._proof_answer(original)
            if proof is not None:
                value,pobj=proof
                p=ParsedRU("exact_proof",{},.995,_norm(original))
                trace=["r710=VERIFIED",f"compiler_rule={pobj['ir'].get('compiler_rule') if pobj.get('ir') else None}"]
                if morph: trace.append(f"r714_lang={morph.get('language')}")
                return self._finish(session_id,p,f"Проверенный вывод: {value}.",evidence=("r710_verified_proof",),organ="r710_proof",trace=trace)

        # R7.6 exact semantic-memory retrieval, only inside frozen neighborhood.
        if parsed.intent=="unknown" and self.exact_v2:
            sem=self.exact_v2.semantic_answer(original)
            if sem:
                p=ParsedRU("exact_semantic",{},float(sem.get("similarity",0.0)),_norm(original))
                tr=[f"r76_atom={sem['atom_id']}",f"r76_similarity={sem['similarity']:.3f}"]
                if morph: tr.append(f"r714_lang={morph.get('language')}")
                return self._finish(session_id,p,str(sem["answer"]),evidence=("r76_frozen_semantic_atom",),organ="r76_semantic_memory",trace=tr)

        # Multi-hop causal query.
        if parsed.intent=="causal_query":
            path=self._causal_path(session_id,parsed.slots.get("effect",""))
            p=ParsedRU("causal_query",parsed.slots,parsed.confidence,parsed.normalized)
            if path:
                tr=[f"causal_hops={len(path)}"]
                if morph: tr.append(f"r714_lang={morph.get('language')}")
                return self._finish(session_id,p,self._render_causal_path(path),evidence=("causal_memory","multi_hop"),organ="causal_graph",trace=tr)
            tr=["causal_hops=0"]
            if morph: tr.append(f"r714_lang={morph.get('language')}")
            return self._finish(session_id,p,self.renderer.render("evidence_missing"),abstained=True,evidence=("causal_memory_miss",),organ="causal_graph",trace=tr)

        # Delegate normal Russian runtime.
        out=super().answer(text,session_id)

        # Focus tracking for later anaphora.
        if out.intent=="world_update":
            pp=self.parser.parse(text)
            self._remember_focus(session_id,pp.slots.get("entity",""))
        elif out.intent=="relation_transfer":
            pp=self.parser.parse(text)
            self._remember_focus(session_id,pp.slots.get("dst",""))

        # Append verified MorphoLex provenance without changing answer.
        if morph and morph.get("used"):
            out.trace=tuple(out.trace)+(f"r714_lang={morph.get('language')}",)
            if morph.get("language")=="ru":
                out.evidence=tuple(out.evidence)+("r714_morpholex",)
        return out
