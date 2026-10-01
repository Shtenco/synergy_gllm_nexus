from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import re
from typing import Any, Protocol

from nexus_gllm.unified_v3.contracts import TaskOpcode, TaskProgram

_IDENT = re.compile(r"[A-Za-zА-Яа-яЁё0-9_.:-]{1,128}")
_HEX64 = re.compile(r"[0-9a-f]{64}")


class SourceKind(str, Enum):
    PROMPT = "PROMPT"
    HISTORY = "HISTORY"
    DOCUMENT = "DOCUMENT"


class TrustClass(str, Enum):
    USER_ASSERTED = "USER_ASSERTED"
    DOCUMENT_ASSERTED = "DOCUMENT_ASSERTED"
    VERIFIED_EVIDENCE = "VERIFIED_EVIDENCE"
    MODEL_PROPOSAL = "MODEL_PROPOSAL"


@dataclass(frozen=True)
class SourceEnvelope:
    source_id: str
    source_kind: SourceKind
    ordinal: int
    text: str
    sha256: str
    trust_class: TrustClass


@dataclass(frozen=True)
class GroundedSpanRef:
    source_id: str
    start: int
    end: int
    sha256: str


@dataclass(frozen=True)
class GeneralizedSemanticAtomProposal:
    operator_id: str
    arguments: tuple[str, ...]
    polarity: bool
    confidence: float
    supporting_spans: tuple[GroundedSpanRef, ...]


@dataclass(frozen=True)
class GeneralizedTaskProposal:
    opcode: TaskOpcode
    operator_id: str | None
    arguments: tuple[str, ...]
    confidence: float
    supporting_spans: tuple[GroundedSpanRef, ...]


@dataclass(frozen=True)
class GeneralizedIngressProposal:
    backend_id: str
    semantic_atoms: tuple[GeneralizedSemanticAtomProposal, ...] = ()
    task: GeneralizedTaskProposal | None = None
    program: Any | None = None


@dataclass(frozen=True)
class GeneralizedIngressRequest:
    sources: tuple[SourceEnvelope, ...]

    @staticmethod
    def _source(source_id: str, kind: SourceKind, ordinal: int, text: str, trust: TrustClass) -> SourceEnvelope:
        return SourceEnvelope(
            source_id,
            kind,
            ordinal,
            text,
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
            trust,
        )

    @classmethod
    def from_texts(
        cls,
        prompt: str,
        history: tuple[str, ...] = (),
        documents: tuple[str, ...] = (),
    ) -> "GeneralizedIngressRequest":
        sources = [cls._source("prompt:0", SourceKind.PROMPT, 0, prompt, TrustClass.USER_ASSERTED)]
        sources.extend(
            cls._source(f"history:{i}", SourceKind.HISTORY, i, text, TrustClass.USER_ASSERTED)
            for i, text in enumerate(history)
        )
        sources.extend(
            cls._source(f"document:{i}", SourceKind.DOCUMENT, i, text, TrustClass.DOCUMENT_ASSERTED)
            for i, text in enumerate(documents)
        )
        return cls(tuple(sources))

    @property
    def source_map(self) -> dict[str, SourceEnvelope]:
        return {source.source_id: source for source in self.sources}


@dataclass(frozen=True)
class GeneralizedIngressAdmission:
    accepted: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class GeneralizedIngressResult:
    semantic_atoms: tuple[GeneralizedSemanticAtomProposal, ...] = ()
    task: TaskProgram | None = None
    task_proposal: GeneralizedTaskProposal | None = None
    program: Any | None = None
    backend_id: str = ""
    admission: GeneralizedIngressAdmission = GeneralizedIngressAdmission(False, ("not_evaluated",))
    proposal_only: bool = True
    sources: tuple[SourceEnvelope, ...] = ()

    @property
    def source_map(self) -> dict[str, SourceEnvelope]:
        return {source.source_id: source for source in self.sources}


class GeneralizedIngressBackend(Protocol):
    backend_id: str

    def propose(self, request: GeneralizedIngressRequest) -> GeneralizedIngressProposal: ...


class GeneralizedIngressR1:
    def __init__(
        self,
        backend: GeneralizedIngressBackend,
        *,
        semantic_min_confidence: float = 0.75,
        task_min_confidence: float = 0.80,
        max_semantic_atoms: int = 64,
        max_args: int = 8,
    ):
        self.backend = backend
        self.semantic_min_confidence = float(semantic_min_confidence)
        self.task_min_confidence = float(task_min_confidence)
        self.max_semantic_atoms = int(max_semantic_atoms)
        self.max_args = int(max_args)

    @staticmethod
    def _digest(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _validate_sources(self, request: GeneralizedIngressRequest) -> list[str]:
        reasons: list[str] = []
        seen: set[str] = set()
        for i, source in enumerate(request.sources):
            if source.source_id in seen:
                reasons.append("duplicate_source_id")
            seen.add(source.source_id)
            if not source.source_id:
                reasons.append(f"source_{i}:source_id_missing")
            if source.ordinal < 0:
                reasons.append(f"source_{i}:bad_ordinal")
            if self._digest(source.text) != source.sha256:
                reasons.append(f"source_{i}:source_hash_mismatch")
        if not request.sources:
            reasons.append("empty_sources")
        return reasons

    def _span_reasons(
        self,
        span: GroundedSpanRef,
        source_map: dict[str, SourceEnvelope],
        label: str,
    ) -> list[str]:
        source = source_map.get(span.source_id)
        if source is None:
            return [f"{label}:unknown_source_id"]
        if span.start < 0 or span.end <= span.start or span.end > len(source.text):
            return [f"{label}:bad_span_bounds"]
        if not _HEX64.fullmatch(span.sha256):
            return [f"{label}:bad_span_hash"]
        if self._digest(source.text[span.start:span.end]) != span.sha256:
            return [f"{label}:span_hash_mismatch"]
        return []

    def _rejected(self, request: GeneralizedIngressRequest, *, backend_id: str = "", reasons: tuple[str, ...]) -> GeneralizedIngressResult:
        return GeneralizedIngressResult(
            backend_id=backend_id,
            admission=GeneralizedIngressAdmission(False, reasons),
            sources=request.sources,
        )

    def parse(self, request: GeneralizedIngressRequest) -> GeneralizedIngressResult:
        source_reasons = self._validate_sources(request)
        if source_reasons:
            return self._rejected(request, reasons=tuple(sorted(set(source_reasons))))

        try:
            proposal = self.backend.propose(request)
        except Exception as exc:
            return self._rejected(
                request,
                backend_id=getattr(self.backend, "backend_id", type(self.backend).__name__),
                reasons=(f"backend_exception:{type(exc).__name__}",),
            )

        if proposal is None:
            return self._rejected(
                request,
                backend_id=getattr(self.backend, "backend_id", type(self.backend).__name__),
                reasons=("empty_proposal",),
            )

        reasons: list[str] = []
        source_map = request.source_map
        if not proposal.backend_id:
            reasons.append("backend_id_missing")
        if len(proposal.semantic_atoms) > self.max_semantic_atoms:
            reasons.append("too_many_semantic_atoms")

        for i, atom in enumerate(proposal.semantic_atoms):
            if not _IDENT.fullmatch(atom.operator_id):
                reasons.append(f"semantic_{i}:bad_operator_id")
            if not atom.arguments or len(atom.arguments) > self.max_args:
                reasons.append(f"semantic_{i}:bad_arguments")
            if any((not arg) or len(arg) > 256 or any(ord(char) < 32 for char in arg) for arg in atom.arguments):
                reasons.append(f"semantic_{i}:bad_arguments")
            if not (0.0 <= atom.confidence <= 1.0) or atom.confidence < self.semantic_min_confidence:
                reasons.append(f"semantic_{i}:low_confidence")
            if not atom.supporting_spans:
                reasons.append(f"semantic_{i}:missing_provenance")
            for j, supporting_span in enumerate(atom.supporting_spans):
                reasons.extend(self._span_reasons(supporting_span, source_map, f"semantic_{i}:span_{j}"))

        task_program = None
        if proposal.task is not None:
            task = proposal.task
            if not isinstance(task.opcode, TaskOpcode):
                reasons.append("task:invalid_opcode")
            if not (0.0 <= task.confidence <= 1.0) or task.confidence < self.task_min_confidence:
                reasons.append("task:low_confidence")
            if len(task.arguments) > self.max_args or any(
                (not arg) or len(arg) > 256 or any(ord(char) < 32 for char in arg)
                for arg in task.arguments
            ):
                reasons.append("task:bad_arguments")
            if task.operator_id is not None and not _IDENT.fullmatch(task.operator_id):
                reasons.append("task:bad_operator_id")
            if not task.supporting_spans:
                reasons.append("task:missing_provenance")
            for j, supporting_span in enumerate(task.supporting_spans):
                reasons.extend(self._span_reasons(supporting_span, source_map, f"task:span_{j}"))
            if isinstance(task.opcode, TaskOpcode) and task.opcode in (
                TaskOpcode.QUERY_RELATION,
                TaskOpcode.FIND_PROOF,
                TaskOpcode.FIND_MINIMAL_PROOF,
            ) and (not task.operator_id or len(task.arguments) != 2):
                reasons.append("task:relation_query_shape_mismatch")

        if reasons:
            return self._rejected(
                request,
                backend_id=proposal.backend_id,
                reasons=tuple(sorted(set(reasons))),
            )

        if proposal.task is not None:
            task_program = TaskProgram(
                proposal.task.opcode,
                proposal.task.operator_id,
                tuple(argument.casefold() for argument in proposal.task.arguments),
            )

        return GeneralizedIngressResult(
            semantic_atoms=proposal.semantic_atoms,
            task=task_program,
            task_proposal=proposal.task,
            program=proposal.program,
            backend_id=proposal.backend_id,
            admission=GeneralizedIngressAdmission(True, ()),
            proposal_only=True,
            sources=request.sources,
        )
