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
                    "text": source.text,
                }
                for source in request.sources
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _example_source_block(rows) -> str:
        return "SOURCES=" + json.dumps(rows, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _example_output(payload) -> str:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def _few_shot_messages(cls):
        transitive_sources = [
            {"source_id":"prompt:0","source_kind":"PROMPT","text":"Query follows mira oren."},
            {"source_id":"document:0","source_kind":"DOCUMENT","text":"mira follows noah; noah follows oren"},
        ]
        transitive_output = {
            "semantic_atoms":[
                {"operator_id":"follows","arguments":["mira","noah"],"polarity":True,"confidence":0.95,"spans":[{"source_id":"document:0","start":0,"end":17}]},
                {"operator_id":"follows","arguments":["noah","oren"],"polarity":True,"confidence":0.95,"spans":[{"source_id":"document:0","start":19,"end":36}]},
            ],
            "task":{"opcode":"query_relation","operator_id":"follows","arguments":["mira","oren"],"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":24}]},
            "program":{"confidence":0.95,"spans":[{"source_id":"prompt:0","start":0,"end":24}],"node":{"kind":"ATOM","symbol":"rule:transitive:follows","children":[],"params":[]}},
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
            "You are a proposal-only semantic parser for NEXUS. Return one compact strict JSON object only. "
            "Do not answer the user's question. Do not invent or derive semantic facts. Never emit top-level summary or explanatory keys. "
            "The only top-level keys are semantic_atoms, task, program. "
            "Extract explicit binary relation facts from HISTORY and DOCUMENT sources into semantic_atoms: one semantic atom per explicit relation clause. "
            "Never collapse a two-hop chain into a derived semantic atom; derivation belongs only in program. "
            "Each semantic atom normally cites exactly one span containing that explicit clause. Offsets reset independently for every source; start/end are never carried across HISTORY/DOCUMENT boundaries. "
            "Infer the user's typed task from PROMPT. If PROMPT explicitly names a relation token, use it as task.operator_id. "
            "If PROMPT asks generically about a relation and all explicit source facts use one operator, use that source operator. If source facts use different operators, use the generic output relation named by PROMPT. "
            "For a short disputed/check query that names an operator but omits entities, and exactly one explicit binary fact is available, use that fact's two entities as task arguments. Words like disputed/check are not operators. "
            "Do not turn hypothetical IF facts into semantic_atoms. In a COUNTERFACTUAL, ADD_FACT operator/src/dst come only from the IF antecedent, while task arguments come from the query conclusion. "
            "Normalize entity identifiers to stable lowercase IDs; keep relation/operator identifiers lowercase. Preserve consistent identity across sources and languages. "
            "Use source-local Python character offsets exactly as provided by the source text. Never cite a source_id that is not present. "
            "If PROMPT is a metalinguistic or malformed-provenance request rather than a supported semantic task, or provenance cannot be grounded, return exactly {\"semantic_atoms\":[],\"task\":null,\"program\":null}. "
            "Each semantic_atoms item MUST be {\"operator_id\":string,\"arguments\":[string,...],"
            "\"polarity\":boolean,\"confidence\":number,\"spans\":[{\"source_id\":string,\"start\":integer,\"end\":integer},...]}. "
            "task is null or {\"opcode\":string,\"operator_id\":string|null,\"arguments\":[string,...],"
            "\"confidence\":number,\"spans\":[...]}. opcode MUST be one of: "
            "query_relation, select_entity, extract_set, order_tuple, epistemic_status, find_proof, "
            "find_minimal_proof, compare_worlds, counterfactual_query, current_state, historical_state. "
            "For a binary relation query use exactly two arguments [source_entity,target_entity]. "
            "program is null or {\"node\":object,\"confidence\":number,\"spans\":[...]}. "
            "For a two-hop same-relation chain use ATOM symbol rule:transitive:R with exactly one relation identifier after rule:transitive:. Never emit rule:transitive:R:R. "
            "For a two-hop mixed-relation chain use ATOM symbol rule:composition:R1:R2:OUT. "
            "For a hypothetical added fact use COUNTERFACTUAL with child rule and params [[\"kind\",\"ADD_FACT\"],[\"operator\",R],[\"src\",A],[\"dst\",B]], where R/A/B are the IF antecedent. "
            "Program node kinds: ATOM, SEQUENCE, COMPOSE, IF, INHIBIT, TEMPORAL, COUNTERFACTUAL. "
            "Every emitted semantic/task/program object must cite source-local Python character offsets with source_id/start/end. "
            "Keep output minimal: no prose, summaries, duplicated evidence, or unused fields."
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
