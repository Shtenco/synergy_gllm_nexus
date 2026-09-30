# NEXUS-RU-COGNITIVE HARD-OOS-E — natural-distractor one-shot result

## Freeze
- Dataset SHA-256: `93a1e9e3c4c7ebe0302ec6b03a259f866852d50e400fe2d25b790311d7e7eb99`
- Planner checkpoint SHA-256: `62c7bc58fb4285fbd2580e5eb926c3c540163b0370948e1b495d8188cdc16da3`
- Planner parameters: **11,040,270**
- Binder: ArgumentBinderV4
- Executor: CompositionalCognitiveExecutorV4
- Pre-inference seal commit: `3db3db37a547a6b50abea0aba74445b96ad24db8`
- No model/binder/executor changes occurred between seal and first inference.

## One-shot result
- Cognitive-plan accuracy: **93.93%**
- End-to-end answer accuracy: **68.53%**

| Category | Plan | Final answer |
|---|---:|---:|
| natural_ru | 80.67% | 66.67% |
| multi_hop | 75.33% | 36.00% |
| causal | 100.00% | 38.67% |
| memory_context | 83.33% | 53.33% |
| conflicting_memory | 100.00% | 100.00% |
| world_state | 100.00% | 62.67% |
| semantic_graph | 100.00% | 35.33% |
| formal_executable | 100.00% | 100.00% |
| evidence_epistemic | 100.00% | 100.00% |
| mixed_cognitive | 100.00% | 92.67% |

## Interpretation
V4 still overfits explicit distractor markers. More natural parenthetical/reference/contrastive distractors break argument binding even when plan selection remains relatively strong.
The next architecture must learn relevance/role binding instead of filtering with a fixed noise-word list.
