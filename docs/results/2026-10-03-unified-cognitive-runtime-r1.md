# NEXUS Unified Cognitive Runtime R1 — integration evidence

Date: 2026-10-03

## Goal

Unify three previously separate lines without relabelling them:

1. **NEXUS V7.2 neural cognitive cortex** — recovered checkpoint `nexus_ru_cortex_v7_2_i_curriculum.pt`.
2. **CRC-R2 learned closed-loop control** — RPE/credit-driven trainable MetaPolicy.
3. **R1.3-X V2 Russian multi-turn semantics** — memory/world/causal/relation/abstention compatibility layer.

## Real checkpoint evidence

- file: `nexus_ru_cortex_v7_2_i_curriculum.pt`
- bytes: 55,129,383
- SHA-256: `5a2c0c74cc25a9d4a17dc3575e299c8fbd2ed6b7a3115ebba439ba93484cfdfa`
- checkpoint meta name: `NEXUS Russian Cognitive Cortex V7.2 I-Curriculum`
- parameters recorded in checkpoint meta: 13,774,043
- recovered state-dict dimensions:
  - vocab embedding: `16385 x 320`
  - positions: `112 x 320`
  - encoder: 6 Transformer layers, FFN 1536
  - final norm: 320
  - plan head: 14
  - relation head: 2
  - role head: 8
  - temporal head: 3

The checkpoint contains no autoregressive LM head. It is treated as a cognitive encoder, never as a Russian text generator.

## Reconstruction boundary

A PyTorch `state_dict` does not encode the Transformer attention-head count. The adapter therefore carries `reconstruction_nhead` and `reconstruction_exact_source` in every feature result. Current wiring uses `nhead=8` but marks `reconstruction_exact_source=false`. Exact V7.2 training/tokenizer source remains unrecovered.

This is a deliberate scientific boundary: structural integration can proceed, but no neural-Russian quality claim is made until tokenizer/source provenance is recovered.

## Learned MetaPolicy

`LearnedMetaPolicy` consumes V7.2 probability vectors plus uncertainty/novelty/self-reliability/budget/calibration features. It learns a policy over 27 auditable control actions:

`branch_depth(1..3) x branch_fanout(1..3) x expert_top_k(1..3)`.

Observed reward produces RPE; recursive credit scales the policy advantage. Value and policy parameters are updated only when learning is enabled. `frozen_evaluation()` records a parameter hash, disables update, and rejects any parameter mutation.

## Russian dialogue compatibility

The new `R13XDialogueCompat` preserves the recovered behavioral contracts required for the unified runtime:

- session memory store/recall/clear;
- world-state update/query;
- focused-entity anaphora;
- causal-store and multi-hop causal explanation;
- relation transfer/query;
- safe arithmetic;
- epistemic abstention;
- dialogue history.

It is explicitly labelled `r13x_v2_compat`, not byte-identical historical R1.3-X.

## Unified runtime path

```text
Russian text
  -> tokenizer callback
  -> real V7.2 checkpoint adapter
  -> CortexDecisionFeatures
  -> LearnedMetaPolicy
  -> Russian dialogue/governor compatibility layer
  -> Russian response + trace + episode_id
  -> observe(reward, credit)
  -> RPE -> policy/value update
```

## Local TDD result

Final local suite after RED->GREEN fixes:

- **8 passed**
- real 55 MB V7.2 checkpoint loaded by exact SHA
- deterministic repeated inference verified
- head dimensions verified: 14/2/8/3
- wrong checkpoint hash fails closed
- synthetic CI-safe state-dict contract passes
- learned-policy hash changes after reward/credit update
- learned-policy hash remains unchanged during frozen evaluation
- Russian memory/world/anaphora/causal/relation/arithmetic/abstention tests pass
- end-to-end real-checkpoint wiring reaches `observe()` and changes learned policy parameters

## Important benchmark boundary

The end-to-end Russian test currently uses a **wiring-only tokenizer callback**. It is not the historical V7.2 tokenizer and therefore cannot support a claim that V7.2's neural plan/relation/role/temporal outputs are semantically valid for arbitrary Russian text.

Therefore current status is:

- **Unified architecture / wiring:** GREEN locally
- **Real V7.2 binary loading:** GREEN
- **Learned closed-loop update:** GREEN
- **R1.3-X-compatible Russian multi-turn state:** GREEN
- **Exact V7.2 tokenizer provenance:** OPEN
- **Fresh neural-Russian benchmark of the fully unified runtime:** BLOCKED on exact tokenizer/source recovery

## Next gate

Recover the exact V7.2 tokenizer/training source or a byte-bound inference preprocessor. Then freeze a fresh Russian multi-turn benchmark before first open and evaluate the full chain without any wiring-only tokenizer substitution.
