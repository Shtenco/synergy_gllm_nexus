# NEXUS-RU-COGNITIVE HARD-OOS-D — adversarial one-shot result

## Freeze
- Dataset SHA-256: `e79cb9270b31224fffb327000a0e9ff95815e802e245a01d0e1cd23dc8a07179`
- Planner checkpoint SHA-256: `62c7bc58fb4285fbd2580e5eb926c3c540163b0370948e1b495d8188cdc16da3`
- Planner parameters: **11,040,270**
- Pre-inference seal commit: `615fe857f2ec74a82179f1e862ec25a1de6ee38c`
- Stressors: novel paraphrases, irrelevant entities, irrelevant numbers, competing values.
- No model/parser/executor changes between seal and first inference.

## One-shot result
- Cognitive-plan accuracy: **99.40%**
- End-to-end answer accuracy: **77.80%**

| Category | Plan | Final answer |
|---|---:|---:|
| natural_ru | 100.00% | 100.00% |
| multi_hop | 100.00% | 48.67% |
| causal | 100.00% | 98.00% |
| memory_context | 100.00% | 46.00% |
| conflicting_memory | 100.00% | 100.00% |
| world_state | 100.00% | 100.00% |
| semantic_graph | 100.00% | 0.00% |
| formal_executable | 94.00% | 94.00% |
| evidence_epistemic | 100.00% | 100.00% |
| mixed_cognitive | 100.00% | 91.33% |

## Interpretation
The 11M planner generalizes extremely well to the task type under adversarial distractors, but the deterministic executor does not yet bind arguments robustly.
This establishes a clear separation:
1. task/planning recognition is now strong;
2. role/argument binding remains weak;
3. adding planner parameters alone will not fix final-answer reasoning.

The next milestone is an explicit Cognitive IR + Argument Binder that identifies relevant entities, operands, temporal writes and distractors before executing a plan.
HARD-OOS-D becomes development-only after this report. Any tuning after this point requires a new sealed benchmark.
