from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from urllib import request as urllib_request

from nexus_gllm.unified_v3.contracts import TaskOpcode
from .generalized_ingress import (
    GeneralizedIngressProposal,
    GeneralizedSemanticAtomProposal,
    GeneralizedTaskProposal,
    GroundedSpanRef,
)
from .program_ast import ProgramKind, ProgramNode
from .program_proposal import ProgramProposal, decode_program_node


@dataclass(frozen=True)
class LlamaCppModelRef:
    model_path: str
    expected_sha256: str
    endpoint: str = "http://127.0.0.1:8080"
    timeout_s: float = 60.0
    seed: int = 42
    max_tokens: int = 768


class LlamaCppTransport:
    def post_json(self, url, payload, timeout_s):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib_request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=timeout_s) as resp:
            return json.loads(resp.read().decode("utf-8"))


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _task_opcode(value) -> TaskOpcode:
    raw = str(value)
    try:
        return TaskOpcode[raw]
    except KeyError:
        return TaskOpcode(raw)


class LlamaCppGeneralizedIngressBackend:
    """Proposal-only llama.cpp adapter bound to exact GGUF bytes.

    The neural model emits a deliberately shallow typed IR. Recursive NEXUS
    program structure and source-span provenance are compiled deterministically
    here so syntax/offset arithmetic do not consume neural capacity.
    """

    def __init__(self, model_ref: LlamaCppModelRef, transport=None):
        path = Path(model_ref.model_path)
        if not path.is_file():
            raise ValueError("model_file_missing")
        actual = _sha256_file(path)
        if actual != model_ref.expected_sha256:
            raise ValueError("model_sha256_mismatch")
        self.ref = model_ref
        self.verified_model_sha256 = actual
        self.transport = transport or LlamaCppTransport()
        self.backend_id = "llamacpp-generalized-ingress:" + actual[:16]

    @staticmethod
    def _source_block(request) -> str:
        return json.dumps(
            [
                {
                    "source_id": source.source_id,
                    "source_kind": source.source_kind.value,
                    "text": source.text,
                }
                for source in request.sources
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @classmethod
    def _messages(cls, request):
        system = (
            "You are the neural semantic front-end for NEXUS. Return one compact strict JSON object only. "
            "Do not answer the user's question. Do not invent facts. Never emit top-level summary or explanatory keys. "
            "Return exactly the top-level keys semantic_atoms, task, program_recipe. "
            "If nothing supported can be proposed, return exactly {\"semantic_atoms\":[],\"task\":null,\"program_recipe\":null}. "
            "Do NOT emit recursive AST nodes and do NOT calculate character offsets. The deterministic NEXUS compiler does that. "
            "semantic_atoms items use {\"operator_id\":string,\"arguments\":[string,...],\"polarity\":boolean,\"confidence\":number,\"source_ids\":[string,...]}. "
            "operator_id is the relation/predicate token from the source; arguments are entity tokens in source order, lowercase when possible. "
            "task is null or {\"opcode\":string,\"operator_id\":string|null,\"arguments\":[string,...],\"confidence\":number,\"source_ids\":[string,...]}. "
            "For binary relation questions use query_relation with the queried relation and [source_entity,target_entity]. "
            "opcode MUST be one of: query_relation, select_entity, extract_set, order_tuple, epistemic_status, find_proof, find_minimal_proof, compare_worlds, counterfactual_query, current_state, historical_state. "
            "program_recipe is null or a shallow object. Supported kinds: "
            "transitive => {kind:'transitive',operators:[relation],confidence:number,source_ids:[...]}; "
            "composition => {kind:'composition',operators:[left,right,query],confidence:number,source_ids:[...]}; "
            "counterfactual_transitive => {kind:'counterfactual_transitive',operators:[relation],add_fact:[relation,src,dst],confidence:number,source_ids:[...]}. "
            "Choose only source_ids that exist in SOURCES. Do not abstain merely because a supported relation query needs inference. "
            "Keep output minimal and never repeat or nest program structures."
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": "SOURCES=" + cls._source_block(request)},
        ]

    def _call(self, request):
        payload = {
            "messages": self._messages(request),
            "temperature": 0,
            "seed": self.ref.seed,
            "max_tokens": self.ref.max_tokens,
            "response_format": {"type": "json_object"},
        }
        data = self.transport.post_json(
            self.ref.endpoint.rstrip("/") + "/v1/chat/completions",
            payload,
            self.ref.timeout_s,
        )
        try:
            raw = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("malformed_chat_completion") from exc
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("empty_chat_completion")
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
            raise ValueError("invalid_span_bounds")
        digest = hashlib.sha256(source.text[start:end].encode("utf-8")).hexdigest()
        return GroundedSpanRef(source_id, start, end, digest)

    def _spans(self, rows, request):
        if not isinstance(rows, list):
            raise ValueError("spans_must_be_list")
        return tuple(self._span(row, request) for row in rows)

    @staticmethod
    def _source_spans(source_ids, request):
        if not isinstance(source_ids, list) or not source_ids:
            raise ValueError("source_ids_must_be_nonempty_list")
        spans = []
        seen = set()
        for raw_source_id in source_ids:
            source_id = str(raw_source_id)
            if source_id in seen:
                continue
            seen.add(source_id)
            source = request.source_map.get(source_id)
            if source is None:
                raise ValueError("unknown_source_id")
            digest = hashlib.sha256(source.text.encode("utf-8")).hexdigest()
            spans.append(GroundedSpanRef(source_id, 0, len(source.text), digest))
        return tuple(spans)

    @staticmethod
    def _compile_recipe(recipe):
        if not isinstance(recipe, dict):
            raise ValueError("program_recipe_not_object")
        kind = str(recipe.get("kind", ""))
        operators = recipe.get("operators", [])
        if not isinstance(operators, list) or any(not isinstance(x, str) or not x for x in operators):
            raise ValueError("program_recipe_bad_operators")
        if kind == "transitive" and len(operators) == 1:
            return ProgramNode(ProgramKind.ATOM, f"rule:transitive:{operators[0]}")
        if kind == "composition" and len(operators) == 3:
            return ProgramNode(ProgramKind.ATOM, f"rule:composition:{operators[0]}:{operators[1]}:{operators[2]}")
        if kind == "counterfactual_transitive" and len(operators) == 1:
            add_fact = recipe.get("add_fact")
            if not isinstance(add_fact, list) or len(add_fact) != 3 or any(not isinstance(x, str) or not x for x in add_fact):
                raise ValueError("program_recipe_bad_add_fact")
            relation, src, dst = add_fact
            if relation != operators[0]:
                raise ValueError("program_recipe_operator_mismatch")
            child = ProgramNode(ProgramKind.ATOM, f"rule:transitive:{operators[0]}")
            return ProgramNode(
                ProgramKind.COUNTERFACTUAL,
                children=(child,),
                params=(("kind", "ADD_FACT"), ("operator", relation), ("src", src), ("dst", dst)),
            )
        raise ValueError("unknown_program_recipe_kind")

    def _decode_legacy_or_typed(self, data, request):
        typed = "program_recipe" in data or any("source_ids" in row for row in data.get("semantic_atoms", []) if isinstance(row, dict))
        if not typed:
            return None

        atoms = []
        for row in data.get("semantic_atoms", []):
            atoms.append(
                GeneralizedSemanticAtomProposal(
                    str(row["operator_id"]),
                    tuple(str(x) for x in row["arguments"]),
                    bool(row.get("polarity", True)),
                    float(row["confidence"]),
                    self._source_spans(row["source_ids"], request),
                )
            )

        task = None
        task_row = data.get("task")
        if task_row is not None:
            operator_id = task_row.get("operator_id")
            task = GeneralizedTaskProposal(
                _task_opcode(task_row["opcode"]),
                None if operator_id is None else str(operator_id),
                tuple(str(x) for x in task_row.get("arguments", [])),
                float(task_row["confidence"]),
                self._source_spans(task_row["source_ids"], request),
            )

        program = None
        recipe = data.get("program_recipe")
        if recipe is not None:
            program = ProgramProposal(
                self._compile_recipe(recipe),
                float(recipe["confidence"]),
                self._source_spans(recipe["source_ids"], request),
            )
        return GeneralizedIngressProposal(self.backend_id, tuple(atoms), task, program)

    def propose(self, request) -> GeneralizedIngressProposal:
        data = self._call(request)
        typed = self._decode_legacy_or_typed(data, request)
        if typed is not None:
            return typed

        # Backward-compatible strict decoder for already frozen legacy contract tests.
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
                _task_opcode(task_row["opcode"]),
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
