# NEXUS-RU-COGNITIVE HARD-OOS-F — 19.2M planner one-shot result

## Freeze
- Dataset SHA-256: `4705c5dedb1e012c413943aa7c7e57c89ef41b050dc725c6bf0bd85e788c28c1`
- Planner checkpoint SHA-256: `bcda5ce85e4bb165748d8c06edf09d061fe1b2f77c6035f2d71cb94299ef37c7`
- Planner parameters: **19,214,734**
- Streaming curriculum examples: **8,960**
- Binder/Executor: V4 unchanged after HARD-OOS-E
- Pre-inference seal commit: `72e5b9f849e3bb19d02644369eb9f0ce722cab5b`
- No model/binder/executor changes between seal and first inference.

## One-shot result
- Cognitive-plan accuracy: **88.87%**
- End-to-end answer accuracy: **57.47%**

| Category | Plan | Final answer |
|---|---:|---:|
| natural_ru | 100.00% | 0.00% |
| multi_hop | 99.33% | 48.00% |
| causal | 62.67% | 0.00% |
| memory_context | 46.67% | 46.67% |
| conflicting_memory | 100.00% | 100.00% |
| world_state | 100.00% | 0.00% |
| semantic_graph | 99.33% | 99.33% |
| formal_executable | 80.67% | 80.67% |
| evidence_epistemic | 100.00% | 100.00% |
| mixed_cognitive | 100.00% | 100.00% |

## Interpretation
Increasing the planner from 11.04M to 19.21M parameters did **not** solve generalization. On new clause-order and reference-sentence structures the unchanged V4 binder/executor remains the dominant bottleneck, while the larger planner also regressed on causal/memory/formal plan selection.

Conclusion:
**parameter count alone is not the path to general Russian reasoning.**
The next model must learn span relevance and semantic roles with order-aware representations (e.g. compact Transformer/sequence encoder), then build a typed Cognitive IR before execution.
