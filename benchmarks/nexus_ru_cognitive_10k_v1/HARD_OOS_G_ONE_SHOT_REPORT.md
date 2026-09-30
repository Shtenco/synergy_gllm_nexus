# NEXUS-RU-COGNITIVE HARD-OOS-G — V6 Cortex one-shot

## Freeze
- Dataset SHA-256: `c7323029e5b4f50f53addfd0fad5cc9a77e645cc0344d0b4cac4166a419cad17`
- Cortex checkpoint SHA-256: `3fac0c7ad40659f5aa7544cc596e5e948bfa7ba183359fc77d42a7501bfe5eab`
- Cortex parameters: **7,455,256**
- Combined cognitive stack (V6 cortex + frozen V5 planner): **26,669,990 parameters**
- Pre-inference seal commit: `27f411c286d3cca893aa98cfe8df4f4616cd86ba`

## One-shot results
- Cognitive plan accuracy: **95.67%**
- Answer-token grounding recall: **74.40%** on 1,199 cases where the gold answer literally appears as a prompt token.

Per-category plan accuracy:
- natural_ru: 100%
- multi_hop: 100%
- causal: 100%
- memory_context: 94.67%
- conflicting_memory: 100%
- world_state: 62%
- semantic_graph: 100%
- formal_executable: 100%
- evidence_epistemic: 100%
- mixed_cognitive: 100%

## Interpretation
V6 substantially improves order-aware task recognition over the 19.2M hashed MLP on fresh structures. The remaining dominant plan weakness is world-state/temporal interpretation.
Grounding recall is only directly meaningful when the final answer is literally present in the input; it should not be interpreted as final-answer accuracy for generated conclusions such as A/B comparisons or epistemic labels.

HARD-OOS-G becomes development-only after this report. Any subsequent training requires a fresh sealed benchmark.
