from __future__ import annotations

from pathlib import Path
import re
import torch

from .answer import AnswerResolver
from .belief import BeliefGraph, BeliefKey, BeliefSnapshot, BeliefUpdate
from .compiler_neural import CompilerCharVocab, NeuralRussianGraphCompiler
from .compiler_proposal import NeuralParseProposal, ProposalValidator
from .compiler_ru import RussianGraphCompiler, _canonical_name
from .consolidation import GraphConsolidator, ConsolidationReport
from .contradiction import ContradictionEngine
from .evidence import EvidenceLedger, EvidenceRecord
from .graph import DynamicHyperGraph
from .persistence import save_graph_json, load_graph_json
from .realizer_ru import DeterministicRussianRealizer, NeuralGraphRealizer, CharVocab, answer_graph_vector
from .recurrent import GraphRecurrentCore
from .rules import RuleEngine
from .schema import AnswerGraph, GLLMResponse, NodeType
from .source_reliability import SourceRegistry, SourceReliability
from .temporal import EventGraphReasoner
from .tensorizer import GraphTensorizer
from .workspace import WorkspaceRetriever


class NexusGLLM:
    CORE_CONFIG = {"node_dim": 32, "edge_types": 8, "hidden_dim": 64, "op_count": 6}
    _BELIEF_PATTERNS = (
        (re.compile(r"^(.+?)\s+старше\s+(.+?)\.?$", re.I), "older_than"),
        (re.compile(r"^(.+?)\s+находится\s+в\s+(.+?)\.?$", re.I), "located_in"),
        (re.compile(r"^(.+?)\s+принадлежит\s+(.+?)\.?$", re.I), "owned_by"),
        (re.compile(r"^(.+?)\s+(?:—\s*)?(?:это|является)\s+(.+?)\.?$", re.I), "is_a"),
    )

    def __init__(self, graph: DynamicHyperGraph | None = None, neural_seed: int = 17, cognition_steps: int = 3) -> None:
        self.graph = graph or DynamicHyperGraph()
        self.compiler = RussianGraphCompiler()
        self.rules = RuleEngine()
        self.resolver = AnswerResolver()
        self.realizer = DeterministicRussianRealizer()
        self.workspace = WorkspaceRetriever()
        self.tensorizer = GraphTensorizer(node_dim=self.CORE_CONFIG["node_dim"], edge_type_buckets=self.CORE_CONFIG["edge_types"])
        self.cognition_steps = cognition_steps
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(neural_seed)
            self.core = GraphRecurrentCore(**self.CORE_CONFIG)
        self.core.eval()
        self.core_checkpoint_info: dict | None = None
        self.neural_realizer: NeuralGraphRealizer | None = None
        self.neural_vocab: CharVocab | None = None
        self.neural_compiler: NeuralRussianGraphCompiler | None = None
        self.compiler_vocab: CompilerCharVocab | None = None
        self.compiler_relations: tuple[str, ...] = ()
        self.compiler_checkpoint_info: dict | None = None
        self.proposal_validator = ProposalValidator(default_threshold=0.80)

        self.evidence_ledger = EvidenceLedger()
        self.source_registry = SourceRegistry()
        self.beliefs = BeliefGraph(self.evidence_ledger, self.source_registry)
        self.contradictions = ContradictionEngine(self.beliefs)

    def load_core_checkpoint(self, path: str | Path) -> dict:
        checkpoint = torch.load(Path(path), map_location="cpu", weights_only=False)
        config = checkpoint.get("config")
        if not isinstance(config, dict):
            raise ValueError("checkpoint config is missing")
        for key, expected in self.CORE_CONFIG.items():
            actual = config.get(key)
            if actual != expected:
                raise ValueError(f"incompatible checkpoint {key}: expected {expected}, got {actual}")
        state_dict = checkpoint.get("state_dict")
        if not isinstance(state_dict, dict):
            raise ValueError("checkpoint state_dict is missing")
        self.core.load_state_dict(state_dict, strict=True)
        self.core.eval()
        self.core_checkpoint_info = {
            "format_version": int(checkpoint.get("format_version", 1)),
            "config": dict(config),
            "seed": checkpoint.get("seed"),
            "epochs": checkpoint.get("epochs"),
        }
        return dict(self.core_checkpoint_info)

    def load_realizer_checkpoint(self, path: str | Path) -> None:
        model, vocab = NeuralGraphRealizer.load_checkpoint(path)
        if model.graph_dim != 32:
            raise ValueError(f"incompatible realizer graph_dim: {model.graph_dim}")
        self.neural_realizer = model
        self.neural_vocab = vocab

    def load_compiler_checkpoint(self, path: str | Path) -> dict:
        model, vocab, relations, meta = NeuralRussianGraphCompiler.load_checkpoint(path)
        if "abstain" not in relations:
            raise ValueError("compiler relation vocabulary must contain abstain")
        unsupported = set(relations) - ProposalValidator.DEFAULT_RELATIONS
        if unsupported:
            raise ValueError(f"compiler checkpoint contains unsupported relations: {sorted(unsupported)}")
        self.neural_compiler = model
        self.compiler_vocab = vocab
        self.compiler_relations = relations
        self.compiler_checkpoint_info = dict(meta)
        return dict(meta)

    def _mark_neural_edge(self, edge_id: str | None, confidence: float) -> None:
        if edge_id and edge_id in self.graph.edges:
            edge = self.graph.edges[edge_id]
            edge.provenance = "compiler:neural:validated"
            edge.confidence = min(edge.confidence, float(confidence))
            edge.metadata["validated_neural_compiler"] = True

    def learn_proposal(self, text: str, proposal: NeuralParseProposal) -> dict:
        validation = self.proposal_validator.validate(text, proposal)
        result = {
            "accepted": validation.accepted,
            "reason": validation.reason,
            "abstention": validation.is_abstention,
            "relation": proposal.relation,
            "confidence": proposal.confidence,
        }
        if not validation.accepted or validation.is_abstention:
            return result

        subject = proposal.subject_text or ""
        obj = proposal.object_text or ""
        edge_id: str | None = None

        if proposal.relation in {"older_than", "located_in", "owned_by", "is_a"}:
            templates = {
                "older_than": f"{subject} старше {obj}",
                "located_in": f"{subject} находится в {obj}",
                "owned_by": f"{subject} принадлежит {obj}",
                "is_a": f"{subject} является {obj}",
            }
            update = self.compiler.compile_statement(templates[proposal.relation], self.graph)
            if update is not None:
                edge_id = update.target_id
            else:
                active = [e for e in self.graph.find_edges(proposal.relation) if e.active]
                if active:
                    edge_id = active[-1].id
        elif proposal.relation in {"before", "after", "causes"}:
            temporal = EventGraphReasoner(self.graph)
            source_id = temporal.ensure_event(subject, confidence=proposal.confidence, provenance="compiler:neural:validated")
            target_id = temporal.ensure_event(obj, confidence=proposal.confidence, provenance="compiler:neural:validated")
            if proposal.relation == "before":
                edge_id = temporal.add_before(source_id, target_id, confidence=proposal.confidence)
            elif proposal.relation == "after":
                edge_id = temporal.add_after(source_id, target_id, confidence=proposal.confidence)
            else:
                edge_id = temporal.add_cause(source_id, target_id, confidence=proposal.confidence)
        else:
            return {**result, "accepted": False, "reason": "relation_not_runtime_mutable"}

        self._mark_neural_edge(edge_id, proposal.confidence)
        self.rules.infer(self.graph)
        return {**result, "edge_id": edge_id}

    def _deterministic_learn_fallback(self, text: str):
        try:
            return self.compiler.compile_statement(text, self.graph)
        except ValueError as ordinary_error:
            try:
                return self.compiler.compile_event_statement(text, self.graph)
            except ValueError:
                raise ordinary_error

    def learn(self, text: str):
        if self.neural_compiler is not None and self.compiler_vocab is not None and self.compiler_relations:
            proposal = self.neural_compiler.predict(text, self.compiler_vocab, self.compiler_relations)
            neural_result = self.learn_proposal(text, proposal)
            if neural_result["accepted"] and not neural_result["abstention"]:
                return neural_result
            try:
                update = self._deterministic_learn_fallback(text)
                self.rules.infer(self.graph)
                return {
                    "accepted": True,
                    "reason": "deterministic_fallback",
                    "neural": neural_result,
                    "update": update,
                }
            except ValueError:
                return neural_result

        update = self._deterministic_learn_fallback(text)
        self.rules.infer(self.graph)
        return update

    def _proposition_from_text(self, text: str) -> BeliefKey:
        clean = " ".join(text.strip().split())
        for pattern, relation in self._BELIEF_PATTERNS:
            match = pattern.match(clean)
            if not match:
                continue
            subject = _canonical_name(match.group(1))
            obj = _canonical_name(match.group(2))
            return BeliefKey(relation, subject, obj)
        raise ValueError(f"unsupported belief observation: {text}")

    def _project_belief_family(self, relation: str, subject: str) -> None:
        candidates = [
            snapshot
            for snapshot in self.beliefs.snapshots()
            if snapshot.key.relation == relation and snapshot.key.subject.casefold() == subject.casefold()
        ]
        if not candidates:
            return
        winner = max(candidates, key=lambda snapshot: (snapshot.posterior, snapshot.key.object))
        if winner.posterior <= 0.5:
            return

        templates = {
            "older_than": f"{winner.key.subject} старше {winner.key.object}",
            "located_in": f"{winner.key.subject} находится в {winner.key.object}",
            "owned_by": f"{winner.key.subject} принадлежит {winner.key.object}",
            "is_a": f"{winner.key.subject} является {winner.key.object}",
        }
        if relation not in templates:
            return
        self.compiler.compile_statement(templates[relation], self.graph)
        # The deterministic compiler already enforces exclusivity for owned_by/located_in.
        # For non-exclusive relations no competing projection is retracted here.
        for edge in self.graph.find_edges(relation, active_only=False):
            if not edge.sources or edge.sources[0] not in self.graph.cards:
                continue
            source_label = self.graph.cards[edge.sources[0]].label
            if source_label.casefold() != winner.key.subject.casefold():
                continue
            if relation in {"owned_by", "located_in"} and edge.targets:
                target_label = self.graph.cards[edge.targets[0]].label
                should_be_active = target_label.casefold() == winner.key.object.casefold()
                if edge.active and not should_be_active:
                    self.graph.retract_edge(edge.id)
                elif should_be_active:
                    edge.active = True
                    edge.metadata["belief_posterior"] = winner.posterior
                    edge.metadata["belief_status"] = winner.status
                    edge.provenance = "belief:projected"

    def observe(
        self,
        text: str,
        *,
        source: str,
        confidence: float = 1.0,
        sequence_index: int | None = None,
        polarity: str = "support",
    ) -> BeliefUpdate:
        key = self._proposition_from_text(text)
        source_state = self.source_registry.get(source)
        record = EvidenceRecord.create(
            proposition_key=key.as_tuple(),
            polarity=polarity,
            source_id=source_state.source_id,
            source_reliability=source_state.reliability,
            confidence=float(confidence),
            sequence_index=sequence_index,
            provenance="runtime:observe",
        )
        update = self.beliefs.observe(record)
        self.contradictions.detect()
        self._project_belief_family(key.relation, key.subject)
        return update

    def belief(self, relation: str, subject: str, object: str | None = None):
        subject_norm = _canonical_name(subject)
        if object is not None:
            return self.beliefs.get(BeliefKey(relation, subject_norm, _canonical_name(object)))
        return [
            snapshot
            for snapshot in self.beliefs.snapshots()
            if snapshot.key.relation == relation and snapshot.key.subject.casefold() == subject_norm.casefold()
        ]

    def correct_source(self, source: str, *, was_correct: bool, weight: float = 1.0) -> SourceReliability:
        return self.source_registry.update(source, was_correct=was_correct, weight=weight)

    def sleep(self) -> ConsolidationReport:
        return GraphConsolidator().run(self.graph)

    def _cognize(self, workspace) -> tuple[float, ...]:
        batch = self.tensorizer.tensorize(self.graph, workspace)
        with torch.no_grad():
            out = self.core(batch, steps=self.cognition_steps)
        return tuple(round(float(v), 8) for v in out.operation_logits[0].cpu())

    def _realize(self, answer, prefer_neural_realizer: bool) -> tuple[str, str]:
        deterministic = self.realizer.realize(answer, self.graph)
        if not prefer_neural_realizer or self.neural_realizer is None or self.neural_vocab is None:
            return deterministic, "deterministic"
        candidate = self.neural_realizer.generate(answer_graph_vector(answer, 32), self.neural_vocab, max_new_tokens=128).strip()
        if answer.answer_value is None:
            return deterministic, "deterministic_fallback"
        if answer.answer_value not in candidate:
            return deterministic, "deterministic_fallback"
        return candidate, "neural_guarded"

    def _answer_event_question(self, text: str) -> AnswerGraph:
        query = self.compiler.compile_event_question(text)
        temporal = EventGraphReasoner(self.graph)

        if query.kind == "temporal_choice":
            left_id = temporal.event_id(query.left or "")
            right_id = temporal.event_id(query.right or "")
            if left_id not in self.graph.cards or right_id not in self.graph.cards:
                return AnswerGraph(None, 0.0, "temporal_choice", provenance="temporal")
            left_before = temporal.before(left_id, right_id)
            if left_before.holds:
                return AnswerGraph(
                    self.graph.cards[left_id].label,
                    left_before.confidence,
                    "temporal_choice",
                    support_node_ids=(left_id, right_id),
                    support_edge_ids=left_before.support_edge_ids,
                    provenance="temporal",
                )
            right_before = temporal.before(right_id, left_id)
            if right_before.holds:
                return AnswerGraph(
                    self.graph.cards[right_id].label,
                    right_before.confidence,
                    "temporal_choice",
                    support_node_ids=(right_id, left_id),
                    support_edge_ids=right_before.support_edge_ids,
                    provenance="temporal",
                )
            return AnswerGraph(None, 0.0, "temporal_choice", provenance="temporal")

        if query.kind == "cause_of":
            target_id = temporal.event_id(query.target or "")
            if target_id not in self.graph.cards:
                return AnswerGraph(None, 0.0, "cause_of", provenance="causal")
            candidates: list[tuple[int, str, tuple[str, ...], float]] = []
            for card in self.graph.cards.values():
                if card.type != NodeType.EVENT or card.id == target_id:
                    continue
                path = temporal.causes(card.id, target_id)
                if path.holds:
                    candidates.append((len(path.support_edge_ids), card.id, path.support_edge_ids, path.confidence))
            if not candidates:
                return AnswerGraph(None, 0.0, "cause_of", provenance="causal")
            _, source_id, support, confidence = sorted(candidates, key=lambda item: (item[0], item[1]))[0]
            return AnswerGraph(
                self.graph.cards[source_id].label,
                confidence,
                "cause_of",
                support_node_ids=(source_id, target_id),
                support_edge_ids=support,
                provenance="causal",
            )

        raise ValueError(f"unsupported event query kind: {query.kind}")

    def ask(self, text: str, prefer_neural_realizer: bool = False) -> GLLMResponse:
        try:
            query = self.compiler.compile_question(text, self.graph)
            self.rules.infer(self.graph)
            answer = self.resolver.resolve(self.graph, query)
        except ValueError:
            answer = self._answer_event_question(text)

        seed_ids = list(answer.support_node_ids)
        ws = self.workspace.retrieve(self.graph, seed_ids, limit=min(128, max(1, len(self.graph.cards))))
        cognition_logits = self._cognize(ws)
        rendered, realizer_mode = self._realize(answer, prefer_neural_realizer)
        return GLLMResponse(
            text=rendered,
            answer_graph=answer,
            workspace_trace=ws.node_ids,
            confidence=answer.confidence,
            cognition_logits=cognition_logits,
            cognition_steps=self.cognition_steps,
            realizer_mode=realizer_mode,
        )

    def save(self, path: str | Path) -> None:
        save_graph_json(self.graph, path)

    @classmethod
    def load(cls, path: str | Path) -> "NexusGLLM":
        return cls(load_graph_json(path))
