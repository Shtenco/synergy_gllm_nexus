# NEXUS-RU-COGNITIVE HARD-OOS-C — sealed one-shot result

## Freeze
- Dataset SHA-256: `39df580da2f77e2167ae5aa18d9a42c01fc23a262fd4ed2a5e7434b57fb98410`
- Planner checkpoint SHA-256: `cfcf621a1c55f6e413ad166f5f91a749d9eccd78f5a53fd1acc8b41fc8ffcd3a`
- Planner parameters: **5,817,998**
- Pre-inference seal commit: `0689a249d5c3480bc951aeaa406b2c2d63065188`
- No parameter/parser/executor changes occurred between seal and first inference.

## One-shot result
- Cognitive-plan accuracy: **92.60%**
- End-to-end answer accuracy: **94.87%**

| Category | Plan | Final answer |
|---|---:|---:|
| natural_ru | 60.00% | 100.00% |
| multi_hop | 84.00% | 98.67% |
| causal | 100.00% | 100.00% |
| memory_context | 86.00% | 86.00% |
| conflicting_memory | 96.00% | 100.00% |
| world_state | 100.00% | 86.67% |
| semantic_graph | 100.00% | 100.00% |
| formal_executable | 100.00% | 100.00% |
| evidence_epistemic | 100.00% | 77.33% |
| mixed_cognitive | 100.00% | 100.00% |

## Interpretation
This is a major improvement over HARD-OOS-B (58.20% routing), especially because the former zero-score families no longer collapse.
However it is **not** sufficient evidence for unrestricted Russian thinking. HARD-OOS-C is synthetic and generated from a controlled task ontology; the executor also contains explicit deterministic procedures for several task families.

The evidence supports a narrower claim:
**NEXUS V2 now demonstrates strong compositional execution and transfer inside this frozen Russian cognitive task family.**

Remaining weaknesses visible before any post-open tuning:
1. evidence/epistemic final-answer execution;
2. memory/context planning and execution;
3. world-state final-answer extraction;
4. plan ambiguity on natural-language lookup and some multi-hop cases.

HARD-OOS-C becomes development-only after this report. Any subsequent tuning requires a new sealed HARD-OOS-D.
