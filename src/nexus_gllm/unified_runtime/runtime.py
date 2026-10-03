from __future__ import annotations
from dataclasses import dataclass
import uuid

from .types import CortexDecisionFeatures, LearnedMetaDecision
from .r13x_dialogue import R13XDialogueCompat, DialogueResponse
from .crc_bridge import CRCOrganBridge, CRCBridgeEpisode, CRCBridgeOutcome


@dataclass(frozen=True)
class UnifiedRuntimeResponse:
    text: str
    episode_id: str
    dialogue: DialogueResponse
    cortex: CortexDecisionFeatures
    meta: LearnedMetaDecision
    trace: tuple[str, ...]


@dataclass(frozen=True)
class UnifiedObserveResult:
    crc: CRCBridgeOutcome
    policy: dict


@dataclass
class _Episode:
    cortex: CortexDecisionFeatures
    meta: LearnedMetaDecision
    novelty: float
    crc_episode: CRCBridgeEpisode


class NexusUnifiedCognitiveRuntime:
    def __init__(self, *, cortex, meta_policy, tokenizer, dialogue=None, crc_bridge=None):
        self.cortex = cortex
        self.meta_policy = meta_policy
        self.tokenizer = tokenizer
        self.dialogue = dialogue or R13XDialogueCompat()
        self.crc = crc_bridge or CRCOrganBridge()
        self.episodes = {}

    def answer(
        self,
        text: str,
        session_id: str = "default",
        *,
        novelty: float = .5,
        self_reliability: float = .5,
        budget_fraction: float = 1.0,
        calibration_pressure: float = 0.0,
    ) -> UnifiedRuntimeResponse:
        cortex_features = self.cortex.infer_text(text, self.tokenizer)
        meta = self.meta_policy.decide(
            cortex_features,
            novelty=novelty,
            self_reliability=self_reliability,
            budget_fraction=budget_fraction,
            calibration_pressure=calibration_pressure,
        )
        dialogue = self.dialogue.answer(text, session_id)
        episode_id = str(uuid.uuid4())
        crc_episode = self.crc.record_decision(
            episode_id=episode_id,
            text=text,
            session_id=session_id,
            dialogue_intent=dialogue.intent,
            cortex=cortex_features,
            meta=meta,
            novelty=novelty,
        )
        self.episodes[episode_id] = _Episode(cortex_features, meta, float(novelty), crc_episode)
        trace = (
            f"cortex=v7.2:{cortex_features.checkpoint_sha256[:12]}",
            f"meta_action={meta.action_index}",
            f"depth={meta.branch_depth}",
            f"fanout={meta.branch_fanout}",
            f"topk={meta.expert_top_k}",
            f"crc_memory={crc_episode.memory_id}",
            f"crc_future={crc_episode.best_branch_id}",
            f"dialogue={dialogue.intent}",
        )
        return UnifiedRuntimeResponse(dialogue.text, episode_id, dialogue, cortex_features, meta, trace)

    def observe(
        self,
        episode_id: str,
        *,
        observed_reward: float,
        information_gain: float = 0.0,
        causal_consistency: float = 0.0,
        progress: float = 0.0,
        calibration_gain: float = 0.0,
        contradiction: float = 0.0,
        compute_cost: float = 0.0,
        risk: float = 0.0,
        counterfactual_credit: dict[str, float] | None = None,
    ) -> UnifiedObserveResult:
        episode = self.episodes.pop(episode_id)
        crc_outcome = self.crc.close_episode(
            episode.crc_episode,
            task_reward=observed_reward,
            information_gain=information_gain,
            causal_consistency=causal_consistency,
            progress=progress,
            calibration_gain=calibration_gain,
            contradiction=contradiction,
            compute_cost=compute_cost,
            risk=risk,
            counterfactual_credit=counterfactual_credit,
        )
        policy_telemetry = self.meta_policy.update(
            episode.cortex,
            action_index=episode.meta.action_index,
            observed_reward=crc_outcome.reward,
            credit=crc_outcome.meta_credit,
            novelty=episode.novelty,
        )
        return UnifiedObserveResult(crc_outcome, policy_telemetry)
