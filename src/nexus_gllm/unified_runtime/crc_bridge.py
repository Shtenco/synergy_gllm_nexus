from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from nexus_gllm.unified_v3.cognitive.credit import CognitiveTraceGraph
from nexus_gllm.unified_v3.cognitive.credit_learning import RecursiveCreditLearner
from nexus_gllm.unified_v3.cognitive.future_tree import BranchValue, FutureTreePlanner
from nexus_gllm.unified_v3.cognitive.memory import HierarchicalMemoryStore
from nexus_gllm.unified_v3.cognitive.reward import RPEngine, RewardVector
from nexus_gllm.unified_v3.cognitive.self_model import NexusSelfModel
from nexus_gllm.unified_v3.cognitive.state import NexusCognitiveState

from .types import CortexDecisionFeatures, LearnedMetaDecision


@dataclass(frozen=True)
class CRCBridgeEpisode:
    state: NexusCognitiveState
    graph: CognitiveTraceGraph
    memory_id: str
    best_branch_id: str | None


@dataclass(frozen=True)
class CRCBridgeOutcome:
    state: NexusCognitiveState
    reward: float
    rpe: float
    credit: dict[str, float]
    meta_credit: float
    memory_id: str
    best_branch_id: str | None


class CRCOrganBridge:
    """Use native CRC-R1 primitives as the feedback spine of the unified runtime.

    The bridge does not replace R1.3-X dialogue state. It records each turn in
    provenance-preserving CRC memory, constructs a FutureTree over policy
    alternatives, builds a cognitive trace, computes RewardVector/RPE, and lets
    RecursiveCreditLearner assign responsibility before the learned MetaPolicy
    is updated.
    """

    def __init__(self):
        self.memory = HierarchicalMemoryStore()
        self.self_model = NexusSelfModel()
        self.credit_learner = RecursiveCreditLearner(self.self_model)
        self.rpe = RPEngine()

    @staticmethod
    def _top_actions(meta: LearnedMetaDecision, n: int) -> tuple[tuple[int, float], ...]:
        ranked = sorted(enumerate(meta.action_probs), key=lambda x: (-x[1], x[0]))
        return tuple((int(i), float(p)) for i, p in ranked[:max(1, int(n))])

    def _future_tree(self, cortex: CortexDecisionFeatures, meta: LearnedMetaDecision):
        top = self._top_actions(meta, meta.branch_fanout)
        planner = FutureTreePlanner(
            max_depth=max(1, int(meta.branch_depth)),
            fanout=max(1, int(meta.branch_fanout)),
            beam_width=max(2, int(meta.branch_fanout) * 2),
        )

        def expand(parent):
            # Reconsider the highest-probability cognitive-control actions at
            # each bounded depth. This is a control tree, not a language tree.
            for idx, prob in top:
                yield f"a{idx}", {"action_index": idx, "prob": prob}, idx

        def evaluate(state: dict[str, Any], action: int, depth: int):
            prob = float(state["prob"])
            return BranchValue(
                expected_reward=prob,
                information_gain=max(0.0, 1.0 - cortex.uncertainty) * 0.10,
                causal_consistency=0.0,
                uncertainty=float(cortex.uncertainty),
                compute_cost=0.02 * float(depth),
                risk=0.0,
            )

        branches = planner.plan({"action_index": meta.action_index}, expand, evaluate)
        return branches, planner.best(branches)

    def record_decision(
        self,
        *,
        episode_id: str,
        text: str,
        session_id: str,
        dialogue_intent: str,
        cortex: CortexDecisionFeatures,
        meta: LearnedMetaDecision,
        novelty: float,
    ) -> CRCBridgeEpisode:
        raw = self.memory.add_raw(
            {
                "episode_id": episode_id,
                "session_id": session_id,
                "text": text,
                "dialogue_intent": dialogue_intent,
                "cortex_sha256": cortex.checkpoint_sha256,
            },
            tags=("unified_runtime", f"session:{session_id}", f"intent:{dialogue_intent}"),
        )
        branches, best = self._future_tree(cortex, meta)

        state = NexusCognitiveState(
            episode_id=episode_id,
            memory_ids=(raw.memory_id,),
            predicted_reward=float(meta.value_estimate),
            uncertainty=float(cortex.uncertainty),
            novelty=float(novelty),
        )
        state = state.transition(
            "learned_meta_control",
            data={
                "action_index": meta.action_index,
                "depth": meta.branch_depth,
                "fanout": meta.branch_fanout,
                "experts": meta.expert_top_k,
                "verification_level": meta.verification_level,
            },
        )
        state = state.transition("memory_record", ref_id=raw.memory_id, data={"level": "RAW"})
        if best is not None:
            state = state.transition(
                "future_plan",
                ref_id=best.branch_id,
                data={"action_index": best.action, "value": best.value.scalar(), "depth": best.depth},
                branch_id=best.branch_id,
            )

        graph = CognitiveTraceGraph()
        graph.add_node("cortex", "cortex", {"capability": "v72_cortex"})
        graph.add_node("learned_meta", "meta", {"capability": "learned_meta_policy", "action_index": meta.action_index})
        graph.add_node("memory", "memory", {"capability": "memory_retrieval", "memory_id": raw.memory_id})
        graph.connect("cortex", "learned_meta", 1.0)
        graph.connect("learned_meta", "memory", 0.35)

        last = "memory"
        if best is not None:
            graph.add_node("future", "branch", {"capability": "future_planning", "branch_id": best.branch_id})
            graph.connect("learned_meta", "future", 0.65)
            graph.connect("memory", "future", 0.35)
            last = "future"

        if dialogue_intent.startswith("causal"):
            graph.add_node("causal", "causal", {"capability": "causal_reasoning"})
            graph.connect(last, "causal", 1.0)
            last = "causal"

        graph.add_node("dialogue", "dialogue", {"capability": "r13x_dialogue", "intent": dialogue_intent})
        graph.connect(last, "dialogue", 1.0)
        graph.add_node("answer", "answer", {"capability": "answer_selection"})
        graph.connect("dialogue", "answer", 1.0)

        return CRCBridgeEpisode(state, graph, raw.memory_id, best.branch_id if best else None)

    def close_episode(
        self,
        episode: CRCBridgeEpisode,
        *,
        task_reward: float,
        information_gain: float = 0.0,
        causal_consistency: float = 0.0,
        progress: float = 0.0,
        calibration_gain: float = 0.0,
        contradiction: float = 0.0,
        compute_cost: float = 0.0,
        risk: float = 0.0,
        counterfactual_credit: dict[str, float] | None = None,
    ) -> CRCBridgeOutcome:
        reward = RewardVector(
            task=float(task_reward),
            information_gain=float(information_gain),
            causal_consistency=float(causal_consistency),
            progress=float(progress),
            calibration_gain=float(calibration_gain),
            contradiction=float(contradiction),
            compute_cost=float(compute_cost),
            risk=float(risk),
        )
        observed = self.rpe.observed(reward)
        rpe = self.rpe.prediction_error(episode.state.predicted_reward, reward)
        graph = episode.graph
        if "outcome" not in graph.nodes:
            graph.add_node("outcome", "outcome", {"capability": "outcome"})
            graph.connect("answer", "outcome", 1.0)
        credit = self.credit_learner.update(
            graph,
            "outcome",
            rpe,
            counterfactual_credit=counterfactual_credit,
        )
        final = episode.state.transition(
            "outcome",
            ref_id="outcome",
            data={"rpe": rpe, "meta_credit": float(credit.get("learned_meta", 0.0))},
            observed_reward=observed,
        )
        return CRCBridgeOutcome(
            state=final,
            reward=observed,
            rpe=rpe,
            credit=credit,
            meta_credit=float(credit.get("learned_meta", 0.0)),
            memory_id=episode.memory_id,
            best_branch_id=episode.best_branch_id,
        )
