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
    """Proposal-only llama.cpp adapter bound to exact GGUF bytes."""

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
                    "char_len": len(source.text),
                    "text": source.text,
                }
                for source in request.sources
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _example_source_block(rows) -> str:
        normalized = [dict(row, char_len=len(row["text"])) for row in rows]
        return "SOURCES=" + json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _example_output(payload) -> str:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def _few_shot_messages(cls):
        transitive_sources = [
            {"source_id":"prompt:0","source_kind":"PROMPT","text":"Is mira related to oren by follows?"},
            {"source_id":"document:0","source_kind":"DOCUMENT","text":"mira follows noah; noah follows oren"},
        ]
        transitive_output = {
            "semantic_atoms":[
                {"operator_id":"follows","arguments":["mira","noah"],"polarity":True,"confidence":0.95,"spans":[{"source_id":"document:0","start":0,"end":17}]},
                {"operator_id":"follows","arguments":["noah","oren"],"polarity":True,"confidence":0.95,"spans":[{"source_id":"document:0","start":19,"end":36}]},
            ],
            "task":{"opcode":"query_relation","operator_id":"follows","arguments":["mira","oren"],"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":35}]},
            "program":{"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":35}],"node":{"kind":"ATOM","symbol":"rule:transitive:follows","children":[],"params":[]}},
        }

        composition_sources = [
            {"source_id":"prompt:0","source_kind":"PROMPT","text":"Is ava connected to cyra?"},
            {"source_id":"document:0","source_kind":"DOCUMENT","text":"ava mentor ben; ben colleague cyra"},
        ]
        composition_output = {
            "semantic_atoms":[
                {"operator_id":"mentor","arguments":["ava","ben"],"polarity":True,"confidence":0.95,"spans":[{"source_id":"document:0","start":0,"end":14}]},
                {"operator_id":"colleague","arguments":["ben","cyra"],"polarity":True,"confidence":0.95,"spans":[{"source_id":"document:0","start":16,"end":34}]},
            ],
            "task":{"opcode":"query_relation","operator_id":"connected","arguments":["ava","cyra"],"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":25}]},
            "program":{"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":25}],"node":{"kind":"ATOM","symbol":"rule:composition:mentor:colleague:connected","children":[],"params":[]}},
        }

        counterfactual_sources = [
            {"source_id":"prompt:0","source_kind":"PROMPT","text":"If Jo ancestor Kai, is Ivy ancestor Kai?"},
            {"source_id":"history:0","source_kind":"HISTORY","text":"ivy ancestor jo"},
        ]
        counterfactual_output = {
            "semantic_atoms":[
                {"operator_id":"ancestor","arguments":["ivy","jo"],"polarity":True,"confidence":0.95,"spans":[{"source_id":"history:0","start":0,"end":15}]},
            ],
            "task":{"opcode":"counterfactual_query","operator_id":"ancestor","arguments":["ivy","kai"],"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":40}]},
            "program":{"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":40}],"node":{"kind":"COUNTERFACTUAL","symbol":"","children":[{"kind":"ATOM","symbol":"rule:transitive:ancestor","children":[],"params":[]}],"params":[["kind","ADD_FACT"],["operator","ancestor"],["src","jo"],["dst","kai"]]}},
        }

        mixed_source_sources = [
            {"source_id":"prompt:0","source_kind":"PROMPT","text":"Query trusts uma wren."},
            {"source_id":"history:0","source_kind":"HISTORY","text":"uma trusts vix"},
            {"source_id":"document:0","source_kind":"DOCUMENT","text":"vix trusts wren"},
        ]
        mixed_source_output = {
            "semantic_atoms":[
                {"operator_id":"trusts","arguments":["uma","vix"],"polarity":True,"confidence":0.95,"spans":[{"source_id":"history:0","start":0,"end":14}]},
                {"operator_id":"trusts","arguments":["vix","wren"],"polarity":True,"confidence":0.95,"spans":[{"source_id":"document:0","start":0,"end":15}]},
            ],
            "task":{"opcode":"query_relation","operator_id":"trusts","arguments":["uma","wren"],"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":22}]},
            "program":{"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":22}],"node":{"kind":"ATOM","symbol":"rule:transitive:trusts","children":[],"params":[]}},
        }

        same_source_sources = [
            {"source_id":"prompt:0","source_kind":"PROMPT","text":"Query guides lex zed."},
            {"source_id":"history:0","source_kind":"HISTORY","text":"lex guides mia; mia guides zed"},
        ]
        same_source_output = {
            "semantic_atoms":[
                {"operator_id":"guides","arguments":["lex","mia"],"polarity":True,"confidence":0.95,"spans":[{"source_id":"history:0","start":0,"end":14}]},
                {"operator_id":"guides","arguments":["mia","zed"],"polarity":True,"confidence":0.95,"spans":[{"source_id":"history:0","start":16,"end":30}]},
            ],
            "task":{"opcode":"query_relation","operator_id":"guides","arguments":["lex","zed"],"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":21}]},
            "program":{"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":21}],"node":{"kind":"ATOM","symbol":"rule:transitive:guides","children":[],"params":[]}},
        }

        conflict_sources = [
            {"source_id":"prompt:0","source_kind":"PROMPT","text":"Check disputed owns fact."},
            {"source_id":"document:0","source_kind":"DOCUMENT","text":"nora owns pax"},
        ]
        conflict_output = {
            "semantic_atoms":[
                {"operator_id":"owns","arguments":["nora","pax"],"polarity":True,"confidence":0.95,"spans":[{"source_id":"document:0","start":0,"end":13}]},
            ],
            "task":{"opcode":"query_relation","operator_id":"owns","arguments":["nora","pax"],"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":25}]},
            "program":{"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":25}],"node":{"kind":"ATOM","symbol":"rule:transitive:owns","children":[],"params":[]}},
        }

        multilingual_sources = [
            {"source_id":"prompt:0","source_kind":"PROMPT","text":"Проверь follows Ава -> Сайра."},
            {"source_id":"document:0","source_kind":"DOCUMENT","text":"Ава follows Бен. Бен follows Сайра."},
        ]
        multilingual_output = {
            "semantic_atoms":[
                {"operator_id":"follows","arguments":["ava","ben"],"polarity":True,"confidence":0.95,"spans":[{"source_id":"document:0","start":0,"end":15}]},
                {"operator_id":"follows","arguments":["ben","cyra"],"polarity":True,"confidence":0.95,"spans":[{"source_id":"document:0","start":17,"end":34}]},
            ],
            "task":{"opcode":"query_relation","operator_id":"follows","arguments":["ava","cyra"],"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":29}]},
            "program":{"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":29}],"node":{"kind":"ATOM","symbol":"rule:transitive:follows","children":[],"params":[]}},
        }

        negative_sources = [
            {"source_id":"prompt:0","source_kind":"PROMPT","text":"Request malformed provenance."},
            {"source_id":"document:0","source_kind":"DOCUMENT","text":"pax knows quin"},
        ]
        negative_output = {"semantic_atoms":[],"task":None,"program":None}

        examples = (
            (transitive_sources, transitive_output),
            (composition_sources, composition_output),
            (counterfactual_sources, counterfactual_output),
            (mixed_source_sources, mixed_source_output),
            (same_source_sources, same_source_output),
            (conflict_sources, conflict_output),
            (multilingual_sources, multilingual_output),
            (negative_sources, negative_output),
        )
        messages = []
        for sources, output in examples:
            messages.append({"role":"user","content":cls._example_source_block(sources)})
            messages.append({"role":"assistant","content":cls._example_output(output)})
        return messages

    @classmethod
    def _messages(cls, request):
        system = (
            "You are the NEXUS proposal parser. Output exactly one compact JSON object with only semantic_atoms, task, program. "
            "PROMPT is query-only: never create semantic facts from PROMPT, including IF antecedents. Semantic facts may come only from explicit HISTORY or DOCUMENT clauses. "
            "Emit one semantic atom per explicit relation clause. Never merge two explicit source clauses into one semantic atom and never replace them with a derived endpoint fact. "
            "Each source has char_len. Offsets reset independently for every source. Every span must satisfy 0 <= start < end <= that exact source char_len and cover only the cited explicit clause. "
            "Normalize entity IDs to lowercase Latin canonical IDs with no surrounding whitespace. Cyrillic proper names should use their common Latin/international canonical form consistently across PROMPT/HISTORY/DOCUMENT. "
            "Never synthesize operator names. A task operator must be the exact relation token explicitly named in PROMPT when present; otherwise use the explicit source operator for a one-relation query, or the generic output relation explicitly named by PROMPT for a mixed-relation composition. Never invent forms such as related_by_parent. "
            "A modifier such as disputed is never an operator. For a short check/disputed query with one explicit fact, use that fact's operator and two entities. "
            "For IF P(A,B), QUERY P(C,B): semantic_atoms contain only real HISTORY/DOCUMENT facts; task is counterfactual_query over the QUERY conclusion; COUNTERFACTUAL ADD_FACT is exactly P(A,B) from the IF antecedent. Never copy an IF fact into a HISTORY/DOCUMENT span. "
            "For same-relation two-hop reasoning, program is ATOM rule:transitive:R with exactly one R. For mixed two-hop reasoning, program is ATOM rule:composition:R1:R2:OUT. "
            "If PROMPT is metalinguistic/unsupported/malformed-provenance rather than a semantic task, return exactly {\"semantic_atoms\":[],\"task\":null,\"program\":null}. "
            "semantic_atoms item schema: {\"operator_id\":string,\"arguments\":[string,...],\"polarity\":boolean,\"confidence\":number,\"spans\":[{\"source_id\":string,\"start\":integer,\"end\":integer},...]}. "
            "task schema: null or {\"opcode\":string,\"operator_id\":string|null,\"arguments\":[string,...],\"confidence\":number,\"spans\":[...]}. Relation tasks require exactly two arguments. "
            "Allowed opcodes: query_relation, select_entity, extract_set, order_tuple, epistemic_status, find_proof, find_minimal_proof, compare_worlds, counterfactual_query, current_state, historical_state. "
            "program schema: null or {\"node\":object,\"confidence\":number,\"spans\":[...]}. Program node kinds: ATOM, SEQUENCE, COMPOSE, IF, INHIBIT, TEMPORAL, COUNTERFACTUAL. "
            "For COUNTERFACTUAL params use [[\"kind\",\"ADD_FACT\"],[\"operator\",R],[\"src\",A],[\"dst\",B]]. No prose or extra keys."
        )
        return [
            {"role":"system","content":system},
            *cls._few_shot_messages(),
            {"role":"user","content":"SOURCES=" + cls._source_block(request)},
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

    def propose(self, request) -> GeneralizedIngressProposal:
        data = self._call(request)
        if (
            not data.get("semantic_atoms")
            and data.get("task") is None
            and data.get("program") is None
        ):
            raise ValueError("empty_neural_proposal")

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
