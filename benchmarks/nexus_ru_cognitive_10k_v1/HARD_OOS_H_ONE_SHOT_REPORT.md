# NEXUS-RU-COGNITIVE HARD-OOS-H — V7 temporal cortex one-shot

## Freeze
- Dataset SHA-256: `9aca4cde35fecf1bdbf0a65debdd8c12892d81e62e7e3860d4594f165d391f1c`
- Cortex checkpoint SHA-256: `e1adb104f67cb17ebc78fd3a8afd394584fc63ad885708e47581d656fb2afbb2`
- Cortex parameters: **13,774,043**
- Combined cognitive stack: **32,988,777 parameters**
- Pre-inference seal commit: `ee7a7a82b9c16d3f63325e923cc0dfca78bfcc56`

## One-shot
- Plan accuracy: **47.07%**
- Answer-token grounding recall: **57.83%** on 1,124 literal-answer cases.
- Current-answer temporal recall: **3.05%** on 525 temporal literal-answer cases.

Per-category plan accuracy:
- natural_ru: 0.00%
- multi_hop: 0.67%
- causal: 8.67%
- memory_context: 99.33%
- conflicting_memory: 0.00%
- world_state: 49.33%
- semantic_graph: 98.00%
- formal_executable: 64.67%
- evidence_epistemic: 50.00%
- mixed_cognitive: 100.00%

## Interpretation
V7's near-perfect in-family validation does not generalize to this newly phrased temporal/anaphoric distribution.
The learned temporal head itself also fails to transfer. This is evidence that the current randomly initialized hashed-subword Transformer is still strongly distribution-bound and should not be described as general Russian language understanding.

HARD-OOS-H becomes development-only after this report. Subsequent tuning requires a fresh sealed benchmark.
