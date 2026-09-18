# NEXUS Reports & Benchmarks Registry

> Canonical registry for the NEXUS / SYNERGY intelligence lineage.  
> Source repository: [Shtenco/synergy_gllm_nexus](https://github.com/Shtenco/synergy_gllm_nexus)  
> Active research branch: [unified-v3-generalization-first](https://github.com/Shtenco/synergy_gllm_nexus/tree/unified-v3-generalization-first)  
> Updated: 2026-09-19

## Scientific status

NEXUS has demonstrated several different kinds of transfer. They must not be collapsed into a single "OOD" number.

| Transfer level | Representative result | Interpretation |
|---|---:|---|
| Surface / paraphrase transfer | R7.6 Blind-23: 56/58 = **96.55%** | strong frozen semantic/paraphrase transfer |
| Unseen operator + support demonstrations | R7-L Blind-18: **3072/3072 = 100%**, 48/48 held-out operators | genuine fast induction / meta-transfer |
| Russian unseen operator + support | R7.2 historical Blind-20: **320/320 = 100% harness-assisted**; autonomous exact replay **254/320 = 79.375%** | saved harness used benchmark-side true intent for final output-head selection; deployable path uses predicted intent |
| Broad post-freeze OOD | R7.18 Blind-31: **156/200 = 78%** | heterogeneous evidence/reasoning transfer |
| Relation/role/graph transfer | Ω-1.5R2 Blind-4 strict triple: **50.37% / 66.63%** | real end-to-end structural transfer, still incomplete |
| Synthetic meta-OOS | v3 P0.1 META-OOS C: **99.44%** | strong transfer inside the same high-level generator family |
| New rule-language / AST basis | HARD-OOS D: **21.91%**, representation failure **100%** | fixed hypothesis representation fails on a new rule grammar |
| Learned MoE routing | v3-MoE P1 useful-expert Top-K recall **99.62%**, negative transfer **0.48%** | routing result on synthetic mixed capability OOS; not yet end-to-end answer accuracy |
| Exact historical MoE federation | NEXUS-MOE-B1: learned **94.44%**, best single **33.33%**, naive-all **59.17%**, oracle **95.83%** | one-shot end-to-end benchmark over 7 exact-runnable historical experts; learned negative transfer **1.45%** |

## Historical benchmark lineage

| Generation / benchmark | Result | Evidence class / caveat |
|---|---:|---|
| V10 600K InfoGraph unseen hash split | **84.83% pass@2** | procedural unseen transfer |
| V30 ARC unseen | **85.92%** | procedural transfer; dialogue remained weak |
| Unified R1.3 compound/open-set | **164/188 = 87.23%**, open-set 30/30 | broad compound result |
| R7-L D192 Blind-18 | **3072/3072 = 100%** | 48 fully held-out operators; no Authority; no inference weight update; support demonstrations allowed |
| R7.2 Blind-20 | historical **320/320 = 100% harness-assisted**; autonomous exact replay **254/320 = 79.375%** | final historical harness selected effect/action head using benchmark-side true intent; exact deployable path exposes intent-classifier bottleneck |
| R7.6 Blind-23 | **56/58 = 96.55%** | post-freeze semantic/paraphrase transfer |
| R7.8 Blind-25 | **77/80 = 96.25%** | frozen architecture-stress transfer |
| R7.9 Blind-26 | **93.33%**, dual 95% | proof/system OOD |
| R7.10 Blind-27 | **150/160 = 93.75%** | fresh eight-domain frozen blind |
| R7.12 Blind-28 | **133/160 = 83.125%** | broad blind |
| R7.16 / R7.17 Blind-30 | **129/200 = 64.5%** | clear generalization gap |
| R7.18 Blind-31 | **156/200 = 78%** | broad post-freeze OOD |
| R7.44 Blind-62 composite | **3066/3200 = 95.81%** | context/state composite |
| R7.44.1 Blind-63 | **2400/2400 = 100%** | context contract |
| R7.44.2 Blind-64 | **2400/2400 = 100%** | context contract |
| R7.44.3 Blind-65 | **2400/2400 = 100%** | context contract; Dialogue-65 25/25 context checks |
| Ω-1.3 surface-disjoint blind | relation **38.61%**, strict graph ~0.60% | early semantic OOD |
| Ω-1.4 Blind-2A / 2B | relation **76.60% / 50.00%** | improved semantic relation transfer |
| Ω-1.5 Blind-3A / 3B | relation **86.20% / 75.10%**; strict triple **5.41% / 1.63%** | relation strong, binding weak |
| Ω-1.5R2 Blind-4A / 4B | strict triple **50.37% / 66.63%** | role/argument binding improvement |
| Unified v2 UB1 | **904/970 = 93.1959%** | exposed-development integration benchmark; not pristine blind |
| Unified v2 UB2 | **2104/2140 = 98.3178%** | regex baseline matched score; paraphrase stress fell to ~26.17%; regression benchmark, not general-intelligence proof |
| NEXUS-FTX1 | **frozen, BLIND unopened** | 2,400 cases, 8 tracks; primary future one-shot far-transfer benchmark |
| v3 P0.1 META-OOS C | **99.44%** | synthetic same-generator-family OOS |
| HARD-OOS D | **21.91%** | independent new AST grammar; consumed after frozen zero-shot |
| v3-MoE P1 | useful recall **99.62%**, negative transfer **0.48%**, strict routing **98.80%** | routing curriculum |
| NEXUS-MOE-B1 | learned **94.44%**; best single **33.33%**; naive/heuristic **59.17%**; oracle **95.83%** | frozen one-shot on real exact historical rollouts; 7/11 requested experts exact-runnable, 4 fail-closed |

## Canonical result reports

All links below point to the active research branch.

1. [2026-09-15 — Ω-1.3 local 100K](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/2026-09-15-omega13-local-100k.md)
2. [2026-09-15 — Ω-1.4 local 100K](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/2026-09-15-omega14-local-100k.md)
3. [2026-09-16 — NEXUS cross-generation audit](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/2026-09-16-nexus-cross-generation-audit.md)
4. [2026-09-16 — Full 78-generation evidence ledger](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/2026-09-16-nexus-full-78-ledger.md)
5. [2026-09-16 — Ω-1.5R2 Blind-4 one-shot JSON](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/2026-09-16-omega15r2-blind4-one-shot.json)
6. [2026-09-16 — Ω-1.6 research-agent landscape](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/2026-09-16-omega16-research-agent-landscape.md)
7. [2026-09-16 — Unified NEXUS rebuild v1](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/2026-09-16-unified-nexus-rebuild-v1.md)
8. [2026-09-17 — FTX1 freeze report](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/2026-09-17-nexus-ftx1-freeze-report.md)
9. [2026-09-17 — Unified v3 P0 report](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/2026-09-17-nexus-unified-v3-p0-report.md)
10. [2026-09-17 — Unified v2 RC1 final](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/2026-09-17-unified-v2-rc1-final.md)
11. [2026-09-18 — Unified v3 P0.1 training report](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/2026-09-18-nexus-unified-v3-p01-training-report.md)
12. [2026-09-18 — HARD-OOS D frozen zero-shot report](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/2026-09-18-nexus-v3-hard-oos-d-zero-shot-report.md)
13. [2026-09-18 — v3-MoE P1 training report](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/2026-09-18-nexus-v3-moe-p1-training-report.md)
14. [2026-09-19 — Artifact-Complete audit + NEXUS-MOE-B1 one-shot](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/2026-09-19-nexus-v3-moe-artifact-complete-b1-report.md)
15. [Unified v2 P0 report](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/UNIFIED_V2_P0_REPORT.md)
16. [Unified v2 P0 / UB1 summary JSON](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/results/UNIFIED_V2_P0_UB1_SUMMARY.json)

## Frozen benchmark manifests and benchmark suites

### CROSSGEN-1
- [CROSSGEN1 freeze manifest](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/crossgen1/CROSSGEN1_FREEZE_MANIFEST.json)
- [CROSSGEN1 schema](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/crossgen1/schema.py)
- Intended panels: RU language, graph, reasoning, context, far transfer, OOD/overfit.

### Ω / Unified frozen manifests
- [Ω-1.4 Blind-2 freeze](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/frozen/OMEGA14_BLIND2_FREEZE_MANIFEST.json)
- [Ω-1.5 Blind-3 freeze](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/frozen/OMEGA15_BLIND3_FREEZE_MANIFEST.json)
- [Ω-1.5R2 preblind final freeze](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/frozen/OMEGA15R2_PREBLIND_FINAL_FREEZE.json)
- [Ω-1.5R2 Blind-4 freeze](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/frozen/OMEGA15R2_BLIND4_FREEZE_MANIFEST.json)
- [Unified rebuild v1 freeze](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/frozen/UNIFIED_REBUILD_V1_FREEZE_MANIFEST.json)
- [Unified rebuild integration benchmark freeze](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/frozen/UNIFIED_REBUILD_V1_INTEGRATION_BENCH_FREEZE.json)
- [Unified rebuild preblind checkpoint freeze](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/frozen/UNIFIED_REBUILD_V1_PREBLIND_CHECKPOINT_FREEZE.json)

### Unified v2 UB2
- [UB2 README](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/ub2/README.md)
- [UB2 freeze manifest](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/ub2/frozen/NEXUS_UB2_FREEZE_MANIFEST.json)
- [Unified v2 preblind freeze](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/ub2/frozen/UNIFIED_V2_PREBLIND_FREEZE.json)
- [Unified v2 source-commit freeze](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/ub2/frozen/UNIFIED_V2_PREBLIND_SOURCE_COMMIT.json)
- [UB2 blind result](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/ub2/results/UNIFIED_V2_UB2_BLIND_RESULT.json)
- [UB2 generator](https://github.com/Shtenco/synergy_gllm_nexus/tree/unified-v3-generalization-first/benchmarks/ub2/generator)
- [UB2 scoring](https://github.com/Shtenco/synergy_gllm_nexus/tree/unified-v3-generalization-first/benchmarks/ub2/scoring)
- [UB2 validators](https://github.com/Shtenco/synergy_gllm_nexus/tree/unified-v3-generalization-first/benchmarks/ub2/validators)

### NEXUS-FTX1
- [FTX1 README](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/ftx1/README.md)
- [FTX1 frozen manifest](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/ftx1/frozen/NEXUS_FTX1_FREEZE_MANIFEST.json)
- [FTX1 public generator](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/ftx1/public_generator.py)
- [FTX1 schema](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/ftx1/schema.py)
- [FTX1 scoring](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/ftx1/scoring.py)
- [FTX1 validators](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/ftx1/validators.py)
- [FTX1 red-team](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/ftx1/redteam.py)
- **Status:** BLIND remains sealed/unopened.

### Generic benchmark runners
- [Belief benchmark](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/run_belief_benchmark.py)
- [General benchmark](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/run_benchmark.py)
- [Compiler benchmark](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/run_compiler_benchmark.py)
- [Consolidation benchmark](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/run_consolidation_benchmark.py)
- [Continual benchmark](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/run_continual_benchmark.py)
- [Forgetting benchmark](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/run_forgetting_benchmark.py)
- [Graph Cortex benchmark](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/run_graph_cortex_benchmark.py)
- [Research benchmark](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/run_research_benchmark.py)
- [Temporal benchmark](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/run_temporal_benchmark.py)
- [Unified v2 preblind UB1 runner](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/run_unified_v2_preblind_ub1.py)

## v3 benchmark/training artifacts

### P0.1 hypothesis-ranker META-OOS
- [Manifest](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_meta/p01_first_hard/manifest.json)
- [Metrics](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_meta/p01_first_hard/metrics.json)
- [Ranker checkpoint](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_meta/p01_first_hard/ranker.pt)

### HARD-OOS D
- [Manifest](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_hard_oos_d/manifest.json)
- [Corpus summary](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_hard_oos_d/corpus_summary.json)
- [Topology inventory](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_hard_oos_d/topology_inventory.json)
- [Zero-shot metrics](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_hard_oos_d/zero_shot_metrics.json)
- [Baselines](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_hard_oos_d/baseline_metrics.json)
- [Consumed marker](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_hard_oos_d/consumed.json)

### v3-MoE P1
- [Manifest](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_moe/p1/manifest.json)
- [Metrics](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_moe/p1/metrics.json)
- [Router checkpoint](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_moe/p1/router.pt)
- [Novelty checkpoint](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_moe/p1/novelty.pt)
- [Calibrator checkpoint](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_moe/p1/calibrator.pt)

### NEXUS-MOE-B1 — exact historical federation
- [Artifact-complete manifest](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/moe_b1/frozen/ARTIFACT_COMPLETE_MANIFEST.json)
- [Frozen split manifest](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/moe_b1/frozen/NEXUS_MOE_B1_FREEZE_MANIFEST.json)
- [Pretest model freeze](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/moe_b1/frozen/NEXUS_MOE_B1_PRETEST_MODEL_FREEZE.json)
- [One-shot result](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/moe_b1/results/NEXUS_MOE_B1_ONE_SHOT_RESULT.json)
- [Aborted seed 2026091907 record](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/benchmarks/moe_b1/results/ABORTED_SEED_2026091907.json)
- [Router checkpoint](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/artifacts/v3_moe/b1/router_b1.pt)
- Status: **7/11 exact-runnable** historical experts. R7.44.3, Ω-1.5R2, V10 and Unified R1.3 remain fail-closed until missing exact bytes/dependencies are mounted.
- Final one-shot: learned MoE **94.44%**, oracle **95.83%**, best fixed single **33.33%**, naive/heuristic **59.17%**; learned negative transfer **1.45%** vs naive **38.26%**.

## Current benchmark policy

- Historical scores are retained with their original scope and caveats.
- A high score is not treated as proof of general intelligence when a simple baseline can reproduce it.
- Few-shot unseen-operator induction and zero-shot extrapolation to a new rule language are distinct capabilities.
- HARD-OOS D is **consumed** and may no longer be used as a clean OOS claim after D-informed training.
- FTX1 BLIND remains sealed.
- NEXUS-MOE-B1 now provides a frozen end-to-end executable-expert benchmark for the 7 exact-runnable historical experts.
- The next artifact milestone is 11/11 exact-runnable recovery; the next scientific transfer milestone must use a fresh B2/FAR-OOS family not used for B1 router training.

## Canonical architecture documents

- [CROSSGEN-1 design](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/superpowers/specs/2026-09-16-crossgen1-unified-nexus-benchmark-design.md)
- [Unified v2 UB2 design](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/superpowers/specs/2026-09-16-nexus-unified-v2-ub2-design.md)
- [FTX1 design](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/superpowers/specs/2026-09-17-nexus-ftx1-design.md)
- [Unified v3 Generalization-First design](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/superpowers/specs/2026-09-17-nexus-unified-v3-generalization-first-design.md)
- [v3 P0.1 Hypothesis Engine + training design](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/superpowers/specs/2026-09-18-nexus-unified-v3-p01-hypothesis-engine-training-design.md)
- [HARD-OOS D design](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/superpowers/specs/2026-09-18-nexus-v3-hard-oos-d-zero-shot-design.md)
- [v3-MoE Generalization Federation design](https://github.com/Shtenco/synergy_gllm_nexus/blob/unified-v3-generalization-first/docs/superpowers/specs/2026-09-18-nexus-v3-moe-generalization-federation-design.md)
