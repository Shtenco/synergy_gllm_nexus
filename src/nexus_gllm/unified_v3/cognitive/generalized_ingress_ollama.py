from __future__ import annotations

import hashlib
import json
import re

from nexus_gllm.unified_v3.contracts import TaskOpcode
from .generalized_ingress import (
    GeneralizedIngressProposal,
    GeneralizedSemanticAtomProposal,
    GeneralizedTaskProposal,
    GroundedSpanRef,
)
from .ollama_surface import OllamaModelRef, OllamaTransport
from .program_proposal import ProgramProposal, decode_program_node


_HEX64 = re.compile(r"[0-9a-f]{64}")


class OllamaGeneralizedIngressBackend:
    """One-call neural proposal adapter with zero truth/execution authority."""

    def __init__(self, model_ref: OllamaModelRef, transport=None):
        if not _HEX64.fullmatch(model_ref.digest_sha256):
            raise ValueError("verified model digest required")
        self.ref = model_ref
        self.transport = transport or OllamaTransport()
        self.backend_id = "ollama-generalized-ingress:" + model_ref.model_id

    @staticmethod
    def _source_block(request) -> str:
        rows = [
            {
                "source_id": source.source_id,
                "source_kind": source.source_kind.value,
                "text": source.text,
            }
            for source in request.sources
        ]
        return json.dumps(rows, ensure_ascii=False, separators=(",", ":"))

    def _call(self, request):
        prompt = (
            "Return strict JSON only. Extract typed semantic atoms, the requested task, and an optional typed program AST. "
            "You are proposal-only: do not answer the question and do not invent facts. "
            "Every semantic/task/program item must cite source-local Python character offsets using source_id/start/end. "
            "Top-level schema: semantic_atoms[], task|null, program|null. "
            "Program node kinds are ATOM, SEQUENCE, COMPOSE, IF, INHIBIT, TEMPORAL, COUNTERFACTUAL.\n"
            "SOURCES=" + self._source_block(request)
        )
        payload = {
            "model": self.ref.model_id,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        }
        data = self.transport.post_json(
            self.ref.endpoint.rstrip("/") + "/api/generate",
            payload,
            self.ref.timeout_s,
        )
        raw = data.get("response")
        if not isinstance(raw, str):
            raise ValueError("missing JSON response")
        return json.loads(raw)

    @staticmethod
    def _span(row, request) -> GroundedSpanRef:
        source_id = str(row["source_id"])
        start = int(row["start"])
        end = int(row["end"])
        source = request.source_map.get(source_id)
        if source is None:
            return GroundedSpanRef(source_id, start, end, "0" * 64)
        if start < 0 or end <= start or end > len(source.text):
            raise ValueError("invalid span bounds")
        digest = hashlib.sha256(source.text[start:end].encode("utf-8")).hexdigest()
        return GroundedSpanRef(source_id, start, end, digest)

    def _spans(self, rows, request):
        if not isinstance(rows, list):
            raise ValueError("spans must be a list")
        return tuple(self._span(row, request) for row in rows)

    def propose(self, request) -> GeneralizedIngressProposal:
        data = self._call(request)
        atoms = []
        for row in data.get("semantic_atoms", []):
            atoms.append(
                GeneralizedSemanticAtomProposal(
                    str(row["operator_id"]),
                    tuple(str(x) for x in row["arguments"]),
                    bool(row.get("polarity", True)),
                    float(row["confidence"]),
                    self._spans(row["spans"], request),
                )
            )

        task = None
        task_row = data.get("task")
        if task_row is not None:
            operator_id = task_row.get("operator_id")
            task = GeneralizedTaskProposal(
                TaskOpcode(str(task_row["opcode"])),
                None if operator_id is None else str(operator_id),
                tuple(str(x) for x in task_row.get("arguments", [])),
                float(task_row["confidence"]),
                self._spans(task_row["spans"], request),
            )

        program = None
        program_row = data.get("program")
        if program_row is not None:
            program = ProgramProposal(
                decode_program_node(program_row["node"]),
                float(program_row["confidence"]),
                self._spans(program_row["spans"], request),
            )

        return GeneralizedIngressProposal(
            backend_id=self.backend_id,
            semantic_atoms=tuple(atoms),
            task=task,
            program=program,
        )
