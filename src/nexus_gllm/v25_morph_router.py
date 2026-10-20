"""NEXUS-Ω V25: Russian morphological routing with evidence-first authority.

Integrates historical R7.14 MorphoLex, R7.44-inspired context and Unified-v2
AnswerGraph/SurfaceDecoder. A V24 generator can suggest wording, but does not
become a factual authority. No pretrained checkpoint is embedded here.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Callable, Protocol

from nexus_gllm.unified_v2.contracts import AnswerGraph, Claim, EntityRef
from nexus_gllm.unified_v2.guard import SemanticConsistencyGuard
from nexus_gllm.unified_v2.organs.context_cortex import ContextCortexV2
from nexus_gllm.unified_v2.organs.morpholex import MorpholexAdapter
from nexus_gllm.unified_v2.organs.surface_decoder import NativeRussianSurfaceDecoderV2


class Morphology(Protocol):
    def canonicalize(self, text: str, lang: str | None = None) -> str: ...
    def analyze(self, text: str, lang: str | None = None): ...


@dataclass(frozen=True)
class VerifiedFact:
    subject: str
    relation: str
    object: str
    topic: str
    provenance: str
    authority: str


@dataclass(frozen=True)
class VerifiedAnswer:
    question: str
    answer: str
    provenance: str
    authority: str


@dataclass(frozen=True)
class LanguageResponse:
    text: str
    route: str
    status: str
    source: str
    trace: tuple[str, ...]
    morphology_active: bool


class RussianMorphRouter:
    """Evidence-first gateway. Always fail closed if a needed source is missing.

    No arbitrary SFT answer is treated as a verified fact. Callers may register
    separately verified QA/facts with evidence and authority; never preload
    test labels or use the sealed evaluation set for routing.
    """

    ALLOWED_AUTHORITIES = frozenset(("formal_authority", "evidence_governor"))
    RELATIONS = {
        "где находится": "located_in",
        "в каком городе находится": "located_in",
        "кому принадлежит": "owned_by",
        "за что отвечает": "отвечает_за",
        "что содержит": "contains",
    }
    NO_ANSWER = "Недостаточно подтверждённых данных для точного ответа."
    AMBIGUOUS = "Нужно уточнить, о каком объекте идёт речь."

    def __init__(
        self,
        *,
        morph_root: str | Path | None = None,
        morphology: Morphology | None = None,
        v24_generate: Callable[[str], str] | None = None,
        candidate_verifier: Callable[[str, str], bool] | None = None,
    ):
        if morph_root is not None and morphology is not None:
            raise ValueError("Set either morph_root or morphology, not both")
        # A historical artifact is executable code + serialized objects:
        # load ONLY when the user trusts its provenance and pinned SHA-256.
        self.morphology = morphology if morphology is not None else (
            MorpholexAdapter(Path(morph_root)) if morph_root is not None else None
        )
        self.context = ContextCortexV2()
        self.surface = NativeRussianSurfaceDecoderV2()
        self.guard = SemanticConsistencyGuard()
        self.v24_generate = v24_generate
        self.candidate_verifier = candidate_verifier
        self.facts: dict[tuple[str, str, str], list[VerifiedFact]] = {}
        self.qas: dict[tuple[str, str], list[VerifiedAnswer]] = {}

    @staticmethod
    def _simple_normalize(text: str) -> str:
        clean = str(text).strip().casefold().replace("ё", "е")
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip(" \t\r\n.!?")

    def _normalize(self, text: str) -> str:
        simple = self._simple_normalize(text)
        if self.morphology is None:
            return simple
        result = self.morphology.canonicalize(simple, "ru")
        if not isinstance(result, str) or not result.strip():
            raise ValueError("R7.14 canonicalize must return non-empty text")
        return self._simple_normalize(result)

    @classmethod
    def _verify_provenance(cls, authority: str, provenance: str) -> None:
        if authority not in cls.ALLOWED_AUTHORITIES:
            raise ValueError("Unrecognized fact authority")
        if not str(provenance).strip():
            raise ValueError("Verified knowledge requires source provenance")

    def add_verified_fact(
        self, subject: str, relation: str, object: str, *,
        provenance: str, authority: str, topic: str = "default",
    ) -> None:
        self._verify_provenance(authority, provenance)
        if not all((subject.strip(), relation.strip(), str(object).strip())):
            raise ValueError("Incomplete fact")
        fact = VerifiedFact(subject, relation, str(object), topic, provenance, authority)
        key = (topic, relation, self._normalize(subject))
        bucket = self.facts.setdefault(key, [])
        if fact not in bucket:
            bucket.append(fact)
        self.context.remember(
            relation + ":" + self._normalize(subject), str(object),
            topic=topic, revision=len(bucket) > 1,
        )

    def add_verified_qa(
        self, question: str, answer: str, *,
        provenance: str, authority: str, topic: str = "default",
    ) -> None:
        self._verify_provenance(authority, provenance)
        if not question.strip() or not answer.strip():
            raise ValueError("Empty QA pair")
        key = (topic, self._normalize(question))
        item = VerifiedAnswer(question, answer, provenance, authority)
        if item not in self.qas.setdefault(key, []):
            self.qas[key].append(item)

    def mention(self, entity_id: str, label: str, *,
                gender: str | None = None, topic: str = "default") -> None:
        self.context.mention_entity(entity_id, label, gender=gender, topic=topic)

    def topic_boundary(self, topic: str) -> None:
        self.context.hard_boundary(topic)

    def _reply(self, text: str, route: str, status: str,
               source: str, trace: list[str]) -> LanguageResponse:
        return LanguageResponse(
            text=text, route=route, status=status, source=source,
            trace=tuple(trace), morphology_active=self.morphology is not None,
        )

    def _fact_answer(self, question: str, topic: str, trace: list[str]):
        lowered = self._simple_normalize(question)
        for prefix, relation in self.RELATIONS.items():
            if not lowered.startswith(prefix + " "):
                continue
            subject_text = lowered[len(prefix):].strip(" .!?")
            # Resolution is topic-scoped; ambiguous reference must never be guessed.
            if subject_text in {"он", "она", "оно", "его", "ее", "её"}:
                res = self.context.resolve_anaphora(subject_text, topic=topic)
                if res.clarification_required or res.entity_id is None:
                    trace.append("anaphora:ambiguous")
                    return self._reply(self.AMBIGUOUS, "context", "clarification",
                                       "r744_context", trace)
                subject_text = res.entity_id
                trace.append("anaphora:resolved")
            matches = self.facts.get((topic, relation, self._normalize(subject_text)), [])
            if not matches:
                return None
            values = {self._normalize(f.object) for f in matches}
            if len(values) != 1:
                trace.append("conflicting_verified_facts")
                return self._reply(self.AMBIGUOUS, "fact", "conflict",
                                   "evidence_governor", trace)
            chosen = matches[0]
            claim = Claim(
                claim_id="v25:" + relation,
                subject=EntityRef(self._normalize(subject_text), chosen.subject),
                relation=relation,
                object=chosen.object,
                confidence=1.0,
                provenance=tuple(f.provenance for f in matches),
                authority=chosen.authority,
            )
            graph = AnswerGraph(claims=(claim,))
            rendered = self.surface.render(graph)
            guard = self.guard.check(graph, rendered)
            if not guard.ok:
                trace.append("semantic_guard:" + ",".join(guard.violations))
                return self._reply(self.NO_ANSWER, "fact", "rejected",
                                   "semantic_guard", trace)
            trace.append("verified_fact:" + chosen.provenance)
            return self._reply(rendered, "fact", "verified",
                               "r714+r744+surface_v2", trace)
        return None

    def answer(self, question: str, *, topic: str = "default") -> LanguageResponse:
        if not question.strip():
            return self._reply(self.NO_ANSWER, "none", "abstain",
                               "input_guard", ["empty_question"])
        trace = ["morph:r714" if self.morphology else "morph:unavailable"]
        # Fail closed if a pinned original R7.14 organ throws or changes API.
        try:
            norm = self._normalize(question)
        except Exception as exc:
            return self._reply(self.NO_ANSWER, "morph", "error",
                               "r714", trace + ["morphology_error:" + type(exc).__name__])
        matches = self.qas.get((topic, norm), [])
        if matches:
            if len({self._simple_normalize(m.answer) for m in matches}) != 1:
                return self._reply(self.AMBIGUOUS, "exact_qa", "conflict",
                                   "evidence_governor", trace + ["conflicting_verified_qa"])
            return self._reply(matches[0].answer, "exact_qa", "verified",
                               matches[0].provenance, trace + ["verified_exact_qa"])
        factual = self._fact_answer(question, topic, trace)
        if factual is not None:
            return factual

        # V24 is a candidate-only generator. No external verifier = no authority.
        if self.v24_generate is not None:
            trace.append("v24:candidate")
            try:
                candidate = self.v24_generate(question)
                if (isinstance(candidate, str) and candidate.strip()
                        and self.candidate_verifier is not None
                        and self.candidate_verifier(question, candidate)):
                    return self._reply(candidate.strip(), "v24", "externally_verified",
                                       "v24+external_verifier", trace + ["verified_by_caller"])
            except Exception as exc:
                trace.append("v24_error:" + type(exc).__name__)
            trace.append("v24:rejected")
        return self._reply(self.NO_ANSWER, "abstain", "unverified",
                           "evidence_governor", trace)
