# NEXUS v3-MoE — Artifact-Complete Audit + NEXUS-MOE-B1 One-Shot Report

**Date:** 2026-09-19  
**Repository:** `Shtenco/synergy_gllm_nexus`  
**Branch:** `unified-v3-generalization-first`  
**Status:** exact-runnable federation benchmark completed; 7/11 requested historical experts runnable from exact artifacts.

## 1. Objective

Replace reconstructed historical donors with exact frozen NEXUS artifacts wherever the original bytes and runtime are available, then measure whether a learned MoE federation produces a real end-to-end gain over individual historical experts and naive ensembling.

This report does **not** claim that all requested historical NEXUS generations were recovered. Missing binaries and missing transitive dependencies remain fail-closed.

## 2. Artifact audit

### EXACT_RUNNABLE

| Expert | Exact material | Verification |
|---|---|---|
| R7-L D192 | three frozen checkpoints 711/712/713 | all SHA-256 match; original architecture loaded |
| R7.2 | `r72_language_binder.pt` + frozen R7-L seed712 | both SHA-256 match; deployable predicted-intent path loaded |
| R7.6 | semantic knowledge organ pickle | SHA-256 matches freeze manifest |
| R7.8 | frozen Blind-25 archive | archive SHA-256 matches; native authority source runnable |
| R7.10 | proof-first freeze | archive SHA-256 matches; original formal runtime runnable |
| R7.14 | multilingual MorphoLex freeze | archive SHA-256 matches; original selftest runnable |
| R7.18 | evidence-credit freeze | archive SHA-256 matches; original runtime and selftests runnable |

### Fail-closed / not silently reconstructed

| Expert | Status | Reason |
|---|---|---|
| R7.44.3 | `EXACT_SOURCE_INCOMPLETE_RUNTIME` | final source found, but `nexus_r738_active_x2_semantic` and governor/data dependencies are absent |
| Ω-1.5R2 | `CHECKPOINT_NOT_MOUNTED` | frozen checkpoint SHA-256 is known, binary is not currently mounted |
| V10 600K InfoGraph | `EXACT_SOURCE_INTEGRATION_CHECKPOINT_NOT_MOUNTED` | source/provenance verified in `agi_olga`; checkpoint deliberately excluded from Git and five original parts are not currently mounted |
| Unified R1.3 | `HISTORICAL_RELEASE_NOT_MOUNTED` | sealed historical result exists, exact release archive is not currently mounted |

Therefore the present milestone is **Artifact-Complete audit + exact-runnable federation**, not a false 11/11 artifact-complete claim.

## 3. Historical reproduction checks

### R7-L

Exact three-checkpoint collective was replayed on the historical Blind-18 protocol:

```text
correct                 3072 / 3072
accuracy                100.00%
operators all queries     48 / 48
```

No inference weight update was used.

### R7.14

Original package selftest:

```text
150 / 150 = 100%
```

across EN, ZH, HI, ES, FR, AR, BN, PT, RU and UR.

### R7.18

Original `tests_r718.py`:

```text
old_disclosed_replay       624 / 624
Blind-30 disclosed replay  200 / 200   (development/regression only)
operator smoke               5 / 5
```

The R7.18 archive itself reports that Blind-31 is not contained in that freeze; no missing Blind-31 artifact is fabricated.

## 4. R7.2 historical-metric correction

The exact binder and exact seed712 core reproduce the saved model hashes.

However, independent replay uncovered a benchmark-harness dependency in the historical reported Blind-20 score.

The historical source does two distinct things:

1. predicts the query intent and encodes that predicted intent into Q;
2. later selects the final effect/action output head using the **benchmark-side true `intent` variable** rather than the predicted intent.

With that historical harness reproduced literally, the stored result `320/320 = 100%` is reproduced.

With a deployable path where the model's predicted intent selects the final output head:

```text
autonomous exact replay     254 / 320 = 79.375%
query intent accuracy                  79.375%
query state accuracy                  100.000%
support state accuracy                100.000%
support effect accuracy               100.000%
support action accuracy               100.000%
```

Therefore the old 100% result must be described as **harness-assisted at final head selection**, not as fully autonomous Russian intent routing.

NEXUS-MOE-B1 deliberately uses the deployable predicted-intent path.

## 5. NEXUS-MOE-B1 design

Six executable capability families:

1. `fast_structured` — R7-L exact 3-seed collective;
2. `fast_ru` — R7.2 exact binder/core, broad Blind-20-style Russian surfaces, no gold intent routing;
3. `semantic_memory` — R7.6 exact semantic knowledge organ;
4. `formal_mcq` — R7.8 / R7.10, with R7.18 allowed to contribute;
5. `morpholex` — R7.14 exact language/morphology path;
6. `evidence_credit` — R7.18 exact evidence-credit runtime.

The compared strategies are:

- best fixed single expert;
- naive all-experts;
- heuristic Top-K;
- learned Top-K MoE with learned utility and lineage discount;
- oracle expert selection ceiling.

The learned fusion is **not majority vote**.

Evidence-credit teacher rows are part of the sealed case before evaluation. Rollout code does not read the scorer gold label to generate teacher evidence.

## 6. One aborted attempt

Seed `2026091907` was excluded.

The process was killed by the sandbox after PRETEST freeze and before any result file was persisted.

Recorded status:

```text
ABORTED_AFTER_PRETEST_FREEZE_BEFORE_RESULT_PERSIST
result_file_present = false
test_metrics_observed = false
tuning_after_attempt = false
```

Because execution may have crossed into the test stage before termination, this seed was conservatively discarded rather than reused.

## 7. Pristine one-shot protocol

Fresh seed:

```text
benchmark seed = 2026091913
router seed    = 17
router epochs  = 45

train = 720  (120/family)
dev   = 180  (30/family)
test  = 360  (60/family)
```

Before test execution:

```text
test split SHA-256
2b7aba62b5cfdc000074e8bfa90ed7b5c5fb71fc6bbd983f6444b8ee6afd8204

router logical SHA-256
290b175184c00e8e4748ec583ef50b206944d4858e510c3925b548d3fcbf2eb9

router serialized SHA-256
3de64c24b4946934878036f8f544ecad9cd9b8f7aba8b14d854cd0973b1e07e4

PRETEST freeze SHA-256
2c1c4903e5d51693d804ac259e5772f54f2c7686ee90865b95407a0cce5bcc44
```

Protocol state:

```text
sealed_before_evaluation = true
test_open_count          = 1
tuning_after_test_open   = false
FTX1_BLIND_used          = false
HARD_OOS_D_reused        = false
```

## 8. Final B1 results

| Strategy | Accuracy | Negative transfer |
|---|---:|---:|
| Best fixed single expert (R7.18) | **33.33%** | n/a |
| Naive all-experts | **59.17%** | **38.26%** |
| Heuristic Top-K | **59.17%** | **38.26%** |
| **Learned MoE** | **94.44%** | **1.45%** |
| Oracle expert ceiling | **95.83%** | **0%** |

The learned MoE is:

- **+61.11 percentage points** over the best single fixed expert;
- **+35.27 pp** over naive-all / heuristic Top-K;
- only **1.39 pp below the oracle ceiling**;
- reduces negative transfer from **38.26% to 1.45%**.

This is the first NEXUS MoE result in this line based on real executions of exact historical artifacts rather than synthetic expert-utility labels.

## 9. Per-family result

| Family | Learned MoE | Oracle | Exact specialist |
|---|---:|---:|---|
| evidence_credit | **100%** | 100% | R7.18 100% |
| fast_ru | **75%** | 75% | R7.2 75% |
| fast_structured | **100%** | 100% | R7-L 100% |
| formal_mcq | **100%** | 100% | R7.8/R7.10/R7.18 100% |
| morpholex | **91.67%** | 100% | R7.14 100% |
| semantic_memory | **100%** | 100% | R7.6 100% |

The remaining gap to oracle is concentrated primarily in MorphoLex routing/fusion and in the intrinsic R7.2 predicted-intent limitation.

## 10. Frozen artifact hashes

```text
ARTIFACT_COMPLETE_MANIFEST.json
65a854bdb42bff533353f57e7274fcd2660b1a03ad69d864b4568179cebbda62

NEXUS_MOE_B1_FREEZE_MANIFEST.json
d4f5cba459abfd82c58ab6c58dbd0b41ce192c05671b1db445810c87167d0736

NEXUS_MOE_B1_PRETEST_MODEL_FREEZE.json
2c1c4903e5d51693d804ac259e5772f54f2c7686ee90865b95407a0cce5bcc44

NEXUS_MOE_B1_ONE_SHOT_RESULT.json
eb681c9efa5b0931001f5b0dccd10c95549896af664e1bfe32fda09997d795f1

router_b1.pt
3de64c24b4946934878036f8f544ecad9cd9b8f7aba8b14d854cd0973b1e07e4
```

## 11. Fresh verification

New exact/B1 tests:

```text
18 passed in 17.12s
```

Also:

```text
python -m compileall -q src/nexus_gllm/unified_v3/moe benchmarks/moe_b1
PASS

anti_leak_hits = []
```

Forbidden router shortcuts scanned include benchmark/track/split/gold/renderer/template/answer-index/proof-path identifiers.

## 12. Interpretation

This result supports a narrower but important conclusion:

> when multiple exact historical NEXUS specialists are actually executable, learned capability routing plus weighted lineage-aware fusion can recover most of the available oracle specialist ceiling while avoiding the severe negative transfer produced by naively combining all experts.

It does **not** prove broad far transfer or AGI. B1 intentionally measures capability federation across known exact historical specialists.

The next scientific problem is therefore twofold:

1. recover the four missing exact historical artifacts/dependencies and move from 7/11 to 11/11 exact-runnable federation;
2. after that freeze a fresh B2 / FAR-OOS benchmark whose task families are not the specialist families used to train B1 routing.

FTX1 BLIND remains sealed and untouched.
