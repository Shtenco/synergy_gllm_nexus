# NEXUS-RU-COGNITIVE HARD-OOS-I — V7.1 one-shot

## Freeze
- Dataset SHA-256: `b6b09fec608c97c9dfde7ced2f3fc962330f65bdd382fc46c8277a8755038de7`
- Cortex checkpoint SHA-256: `4b0c75160ada0a485e5d16db84c16814053b61cd66b35413b3ea9338b906d2b3`
- Cortex parameters: **13,774,043**
- Pre-inference seal commit: `2b69601bb5d5e33d49a9a28f792ab1cd908bdcae`

## One-shot
- Plan accuracy: **75.07%**
- Answer-token grounding recall: **79.55%** on 1,198 literal-answer cases.
- Current-answer temporal recall: **55.32%** on 526 temporal cases.

Per-category plan accuracy:
- natural_ru: 0%
- multi_hop: 100%
- causal: 88%
- memory_context: 100%
- conflicting_memory: 34%
- world_state: 100%
- semantic_graph: 100%
- formal_executable: 78.67%
- evidence_epistemic: 50%
- mixed_cognitive: 100%

## Interpretation
H-curriculum transfers materially to a fresh distribution, especially multi-hop, memory, world-state and semantic graph, but general Russian task semantics are still incomplete. HARD-OOS-I becomes development-only after this report.
