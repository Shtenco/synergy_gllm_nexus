# NEXUS Unified v2 RC1 — final frozen report

**Status:** `FROZEN_EXECUTABLE_RC1_GATES_PASS_HARNESS_END_TO_END_UB2_PENDING`  
**Preblind source commit:** `ba23e94886c08a4b83c66ad850410d50cae8e721`  
**Source-freeze record:** `ffca2a74fa3a90c84a656f03886e7973a487687a`

## Verified runtime result

The twelve-slot PREBLIND runtime was re-run after restoring exact donor artifacts without changing source. Full verification is green: **60/60 tests passed**, `compileall` passed, and the fresh UB1 output is byte-identical to the preblind result.

### UB1 — actual single-runtime execution

- Strict correct: **904/970**
- Full Strict: **93.1959%**
- Track Macro: **95.2041%**
- All preregistered UB1 development gates: **PASS**
- Scientific label: `UB1_EXPOSED_DEVELOPMENT` because the semantic supplement was designed after UB1 inspection.

### UB2 — one-shot frozen blind contract harness

- Strict correct: **2104/2140**
- Full: **98.3178%**
- Invalid citations: **0**
- Guard mutations: **0**
- All preregistered harness gates: **PASS**

| Track | Strict |
|---|---:|
| russian_free_dialogue | 100.00% (300/300) |
| long_memory | 100.00% (300/300) |
| russian_coreference | 100.00% (300/300) |
| complex_causality | 100.00% (300/300) |
| research_evidence | 100.00% (300/300) |
| graph_ood_reasoning | 100.00% (320/320) |
| unseen_task_induction | 88.75% (284/320) |

## Critical methodological boundary

The UB2 blind result is valid for the **frozen preregistered contract harness**: its code was frozen before blind opening and was not tuned afterward. However, that harness directly parses the synthetic UB2 task surfaces and **does not route every blind case through all twelve runtime organs end-to-end**. Therefore `98.3178%` must not be reported as a full end-to-end Unified-v2 intelligence score or an AGI result.

The strongest real end-to-end evidence for RC1 is currently the 970-case UB1 single-runtime run (`93.1959%`), with the explicit caveat that UB1 is exposed development data.

## Donor status

- R7.8 formal authority: exact.
- R7.2 Russian binder: exact.
- R7.14 MorphoLex: exact.
- Ω-1.4R / Ω-1.5R2 relation + roles: exact frozen checkpoints.
- R7-L unseen operator: exact.
- R7.17 recurrent reasoner: exact.
- R7.18 evidence semantic runtime: exact.
- Unified Rebuild v1 workspace/checkpoints: exact.
- Ω-1.6 research: exact source blobs from commit `2b6d78d9b955bb892356a6cade50634911f7b13c`.
- Context Cortex v2: rebuilt from R7.44.3 contracts, **not** an exact R7.44.3 restoration.
- Surface Decoder v2: new faithful deterministic renderer protected by semantic guard.

## Correct next experiment

Do **not** tune against opened UB2. The next honest promotion benchmark should be a new frozen **UB3 / UB2-E2E** suite. Its runner must be frozen before blind generation/opening and must send every task through the actual unified runtime API rather than a benchmark-specific regex predictor.