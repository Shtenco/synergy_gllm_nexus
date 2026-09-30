# NEXUS-RU-COGNITIVE-10K V1 — frozen one-shot report

## Protocol
- 10 cognitive categories × 1,000 Russian tasks = 10,000.
- TRAIN: 7,000.
- VALIDATION: 1,500.
- HARD-OOS-A: 1,500 diagnostic tasks.
- HARD-OOS-B: 1,500 independently regenerated tasks used for the decisive one-shot routing test.
- HARD-OOS-B was SHA-256 sealed in Git before first inference.
- No training or threshold tuning occurred after the HARD-OOS-B seal and before its first inference.

## Frozen identifiers
- HARD-OOS-B SHA-256: `918635e4d27b2e49058e3003606d87eeef64637c100b32c25670a655ae2b2394`
- Frozen trained router SHA-256: `883250c0b76a11723d6dcd2008c901cb1879c3e9f3772d841f262d5415bf7514`
- Pre-inference Git freeze commit: `8742c25fc84dbc3ffa0946c56362e65a50d69051`

## Results
### Development / diagnostic
- Validation routing accuracy: 90.00%.
- HARD-OOS-A routing accuracy: 56.53%.

### Decisive one-shot HARD-OOS-B
- Overall routing accuracy: **58.20%**.

Per category:
- natural Russian understanding: 150/150 = 100.00%
- multi-hop reasoning: 0/150 = 0.00%
- causal reasoning: 150/150 = 100.00%
- memory/context: 119/150 = 79.33%
- conflicting-memory: 0/150 = 0.00%
- world-state: 150/150 = 100.00%
- semantic graph: 150/150 = 100.00%
- formal/executable: 4/150 = 2.67%
- evidence/epistemic: 150/150 = 100.00%
- mixed cognitive: 0/150 = 0.00%

## Interpretation
This result does **not** support the claim that the trained router has learned general Russian reasoning.
It supports narrower claims: robust recognition/generalization for several semantic and epistemic families, plus partial memory/context transfer.
The catastrophic failures on multi-hop, conflicting-memory, formal/executable and mixed-composition tasks show that the current learned layer is still strongly dependent on task-family surface structure.

Therefore the status is:
**NO — NEXUS Unified RU V1 has not yet demonstrated general Russian thinking on NEXUS-RU-COGNITIVE-10K V1.**

This is a routing/generalization result, not yet a full end-to-end Qwen3 + all frozen organs answer-quality result.
The next valid milestone is an organ-level compositional executor with fresh sealed HARD-OOS-C, not post-tuning on HARD-OOS-B.
