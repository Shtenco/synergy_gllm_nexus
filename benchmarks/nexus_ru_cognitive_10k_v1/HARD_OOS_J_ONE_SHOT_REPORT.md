# NEXUS-RU-COGNITIVE HARD-OOS-J — V7.2 one-shot

## Freeze
- Dataset SHA-256: `78bc26d461469418357934f30351b936f31186608d49ae1976c4deb0eca9a2a2`
- Cortex checkpoint SHA-256: `5a2c0c74cc25a9d4a17dc3575e299c8fbd2ed6b7a3115ebba439ba93484cfdfa`
- Cortex parameters: **13,774,043**
- Pre-inference seal commit: `5c8869a6393ba840384dbd8bac6db79db1d7c8b8`

## One-shot
- Plan accuracy: **57.47%**
- Answer-token grounding recall: **84.15%** on 1,123 literal-answer cases.
- Current-answer temporal recall: **58.48%** on 525 temporal cases.

Per-category plan accuracy:
- natural_ru: 13.33%
- multi_hop: 2.00%
- causal: 4.67%
- memory_context: 100%
- conflicting_memory: 75.33%
- world_state: 2.00%
- semantic_graph: 100%
- formal_executable: 100%
- evidence_epistemic: 77.33%
- mixed_cognitive: 100%

## Interpretation
Successive H/I curricula improved token grounding and temporal binding, but plan semantics remain strongly distribution-bound. This is a repeatable limitation of the randomly initialized hashed-subword Transformer approach.

Conclusion: the next architecture should initialize the language cortex from a pretrained Russian/multilingual LM (the R2.1/Qwen3 line is the intended candidate), while keeping NEXUS proof/governor layers sovereign.
HARD-OOS-J becomes development-only after this report.
