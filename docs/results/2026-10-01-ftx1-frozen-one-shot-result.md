# NEXUS CRC-R1 — FTX1 frozen one-shot result

**Date:** 2026-10-01  
**Status:** FINAL FIRST OPEN — NO RETRY / NO POST-OPEN TUNING

## Result

```text
FTX1 cases              2400
strict correct             0
full strict             0.00%
macro strict            0.00%
open_count                  1
post-open tuning        FALSE
```

Per track, all eight frozen tracks scored **0/300**:

- semantic_rule_induction — 0/300
- surface_far_transfer — 0/300
- role_voice_coreference — 0/300
- task_schema_induction — 0/300
- compositional_reasoning — 0/300
- cross_language_transfer — 0/300
- long_horizon_transfer — 0/300
- evidence_counterfactual — 0/300

This result is retained exactly as observed. It is not rerun after inspecting gold.

## Frozen identities

- CRC-R1 runtime commit: `fded8bd46777b2e868620b4c85d60c5c375b5ec1`
- runtime tree: `fb6e5ebdfaf09636d603f31d189f6fa735f42670`
- canonical FTX1 ZIP SHA-256: `cd01b1c37cc35ddf970aaffff2a6ae25723e4db1c0421fdccf5c423a35efae56`
- FTX1 runtime JSONL SHA-256: `f19fe25cc839a78966b0b07ce8733f162462d35ab67c8bd73e547ff59a13bebf`
- FTX1 gold JSONL SHA-256: `d2d1f023f03e7b0e960f146feed95631f79351b8e0895d0923e1df9061acf11b`
- generic runner SHA-256: `d3ebfa45a45cbc6c866bfa2ae4a11c5901c0e9c3448985a881b684708a8754b5`
- predictions SHA-256: `7f025d1a9ee7cd50f9bbbd4201a60c0faa2648ad28c8e96316053fe9eaec181c`
- predictions-freeze SHA-256: `3551798e381c926726eb081f4f31cc48f65d59194dfd42ad25f1db64a6bc9691`
- final result SHA-256: `62c6ee5169d57fb977f3f40ea46c27f66fc7abf9c7f61cb0fdb367ad8fdef804`

The sealed manifest independently confirmed 2,400 cases, eight tracks × 300, BLIND seed `33017`, and the same runtime/gold hashes.

## Protocol chronology

1. CRC-R1 `fded8bd...` had already passed validation.v3 and was commit-bound `FROZEN_PRE_FTX1`.
2. Canonical FTX1 ZIP hash was verified before any content access.
3. A generic adapter was committed before BLIND access on branch `ftx1-clean-eval-2026-10-01`.
4. Runner SHA was frozen before opening.
5. Synthetic pre-open check passed against the frozen task-cortex early-exit semantics. The full runtime itself had already passed validation.v3; GitHub-hosted pre-open jobs remained queued and were not used to change the runner.
6. `OPEN_EVENT` set `open_count=1` before the first archive-content access.
7. Only `FTX1_RUNTIME.jsonl` was read first. `FTX1_GOLD.jsonl` remained unopened.
8. Runtime corpus was validated as 2,400 unique cases with exactly the four allowed runtime-visible fields: `case_id`, `prompt`, `history`, `documents`.
9. The frozen `ControlledTaskBackend` accepted **0/2400** BLIND prompts.
10. By the frozen `ConversationalReasonerR1` code, every rejected prompt exits as `UNRESOLVED` before program synthesis. The frozen language ingress is fail-safe on rejected/empty proposals, so history/documents cannot turn a task-parser rejection into a task.
11. Therefore the exact per-case frozen outcome was `answer=None`, `structured=[]`, `epistemic=UNRESOLVED`, `abstain=true`, `citations=[]`. No retry or alternate model was allowed.
12. All 2,400 predictions were materialized and SHA-frozen **before** gold access.
13. Only then was gold read and the public canonical FTX1 strict scorer applied.
14. Predictions were not modified after scoring.

### Important execution note

Because all 2,400 prompts failed the frozen task-cortex gate, the result is determined by an early-exit branch of the frozen runtime. The experiment therefore did not need to execute program synthesis or downstream reasoning for any case. This is semantically equivalent to executing the frozen reasoner on those cases: downstream code is unreachable once `TaskCortexResult.task is None`.

## Why the score is zero

The failure occurs **before the new CRC reasoning machinery is reached**.

The frozen default task cortex recognizes only a narrow controlled Russian query surface. None of the 2,400 BLIND prompts matched that surface. Consequently:

```text
FTX1 natural-language prompt
        ↓
ControlledTaskBackend
        ↓
0 / 2400 admitted
        ↓
UNRESOLVED
        ↓
program synthesis never reached
        ↓
Future Tree / memory / causal / credit machinery never reached
```

All predictions therefore had no answer. FTX1 gold had a non-null answer in **2400/2400** cases, so strict correctness was necessarily zero even before considering the other strict fields.

Component agreement confirms the diagnosis:

```text
answer          0.00%
structured     87.50%
epistemic       3.0833%
abstain         3.0833%
citations      96.8333%
```

## Scientific interpretation

FTX1 falsifies the proposition that this frozen CRC-R1 snapshot is already an end-to-end generalized conversational reasoning system.

It does **not** by itself show that every internal specialist, AST executor, memory system, Future Tree, causal model, or credit mechanism is useless. The blind test never reaches those organs. The dominant failure is the ingress/task-representation boundary between unrestricted FTX1 language and the controlled task cortex.

This also reveals a weakness in the pre-FTX1 validation stack: HARD-OOS F/F2 and META-OOS G proved important internal compositional capabilities, but they did not establish an end-to-end natural-language admission path equivalent to FTX1.

## After opening

FTX1 is now **consumed**. It must never again be described as untouched OOS for this project.

It may now be used only as a diagnostic/development corpus with explicit `CONSUMED_FTX1` labelling. Any future clean claim requires a newly sealed benchmark (for example FTX2) authored and frozen before the next architecture is tested.

## Next engineering target

The evidence points to a precise next milestone rather than adding more internal reasoning machinery:

```text
M32 — Generalized Semantic + Task Ingress

free text / multilingual / history / documents
        ↓
proposal-only neural or learned ingress
        ↓
strict provenance + authority gate
        ↓
typed task/program representation
        ↓
CRC-R1 reasoning organs
```

The next clean benchmark must require that the system actually reaches the reasoning organs; admission/coverage and downstream conditional accuracy should be reported separately.
