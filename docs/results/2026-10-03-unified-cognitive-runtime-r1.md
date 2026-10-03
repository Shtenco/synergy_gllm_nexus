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

Searches by checkpoint name and internal signatures (`16385`, `13,774,043`, `i_curriculum`, `i_plan_acc`, temporal/Russian cortex wording) have not recovered an exact tokenizer/preprocessor source in the currently indexed GitHub/Drive material.

This is a deliberate scientific boundary: structural integration can proceed, but no neural-Russian quality claim is made until tokenizer/source provenance is recovered.

## Learned MetaPolicy

`LearnedMetaPolicy` consumes V7.2 probability vectors plus uncertainty/novelty/self-reliability/budget/calibration features. It learns a policy over 27 auditable control actions:

`branch_depth(1..3) x branch_fanout(1..3) x expert_top_k(1..3)`.

Value and policy parameters are updated only when learning is enabled. `frozen_evaluation()` records a parameter hash, disables update, and rejects any parameter mutation.

## Native CRC organ bridge

The runtime no longer accepts a caller-supplied scalar as the normal learned-policy credit path.

`CRCOrganBridge` now uses the existing CRC-R1 primitives directly:

- `HierarchicalMemoryStore` records each turn as RAW evidence with provenance;
- `FutureTreePlanner` explores bounded cognitive-control alternatives using the learned MetaPolicy probabilities and selected depth/fanout;
- `CognitiveTraceGraph` records `cortex -> learned_meta -> memory/future -> dialogue -> answer -> outcome`;
- causal dialogue turns receive a dedicated causal-responsibility node in the trace;
- `RewardVector` and `RPEngine` compute observed reward and prediction error;
- `RecursiveCreditLearner` propagates responsibility through the trace and updates `NexusSelfModel`;
- only the resulting `credit['learned_meta']` is passed to `LearnedMetaPolicy.update()`.

Therefore the executable feedback chain is now:

```text
Outcome
 -> RewardVector
 -> CRC RPE
 -> CognitiveTraceGraph
 -> RecursiveCreditLearner
 -> learned_meta responsibility
 -> LearnedMetaPolicy.update
 -> changed future policy
```

Counterfactual per-node credit may be supplied to `RecursiveCreditLearner` as an attribution measurement. It is blended by the CRC learner; it is not used as a direct replacement for the final policy credit.

Direct propagation verification with the same CRC equations produced:

- positive RPE example: `credit['learned_meta'] = +0.7597638`
- negative RPE plus counterfactual attribution: `credit['learned_meta'] = -0.6282546`

The self-model credit mass changes with those assignments.

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
  -> LearnedMetaPolicy decision
  -> CRC RAW memory + FutureTree
  -> R1.3-X-compatible Russian dialogue/governor
  -> CognitiveTraceGraph
  -> Russian response + episode_id
  -> observe(reward vector)
  -> CRC RPE
  -> RecursiveCreditLearner
  -> credit[learned_meta]
  -> LearnedMetaPolicy update
```

## Tests and evidence

Earlier local RED->GREEN suite before the deeper CRC bridge:

- **8 passed**
- real 55 MB V7.2 checkpoint loaded by exact SHA
- deterministic repeated inference verified
- head dimensions verified: 14/2/8/3
- wrong checkpoint hash fails closed
- synthetic CI-safe state-dict contract passes
- learned-policy hash changes after update
- learned-policy hash remains unchanged during frozen evaluation
- Russian memory/world/anaphora/causal/relation/arithmetic/abstention tests pass
- end-to-end real-checkpoint wiring reaches `observe()` and changes learned policy parameters

A new checkpoint-independent `test_crc_bridge.py` additionally requires on GitHub/CI:

- RAW memory provenance is preserved;
- FutureTree produces a branch;
- positive outcome produces positive `learned_meta` recursive credit;
- negative/counterfactual outcome produces negative `learned_meta` credit;
- self-model accumulates the credit mass.

GitHub Actions for the current branch are presently queued; CI is **not** labelled GREEN until the hosted runner actually executes and reports success.

## Important benchmark boundary

The end-to-end Russian wiring test currently uses a **wiring-only tokenizer callback**. It is not the historical V7.2 tokenizer and therefore cannot support a claim that V7.2's neural plan/relation/role/temporal outputs are semantically valid for arbitrary Russian text.

Therefore current status is:

- **Unified architecture / wiring:** GREEN locally for the previously executed 8-test suite
- **Real V7.2 binary loading:** GREEN locally
- **Native CRC memory/FutureTree/RPE/recursive-credit path:** IMPLEMENTED; CI test queued
- **Learned policy driven by CRC-derived meta credit:** IMPLEMENTED; direct propagation verified; CI queued
- **R1.3-X-compatible Russian multi-turn state:** GREEN locally for the previously executed suite
- **Exact V7.2 tokenizer provenance:** OPEN
- **Fresh neural-Russian benchmark of the fully unified runtime:** BLOCKED on exact tokenizer/source recovery

## Next gates

1. Obtain an executed GitHub CI result for the new CRC-bridge tests; do not infer GREEN from queue state.
2. Recover the exact V7.2 tokenizer/training source or a byte-bound inference preprocessor.
3. Freeze fresh Russian multi-turn cases before first open.
4. Run the full unified runtime with parameter hashes locked during evaluation and preserve raw transcripts/category metrics.
5. Only after that evaluate whether the integrated learned loop improves fresh Russian/OOD performance rather than merely proving wiring.
