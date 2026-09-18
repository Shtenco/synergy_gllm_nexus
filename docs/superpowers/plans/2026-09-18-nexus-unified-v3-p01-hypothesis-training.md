# NEXUS Unified v3 P0.1 Hypothesis Engine + Synthetic Training Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend Unified v3 P0 into a bounded competing-hypothesis reasoning engine, then train and evaluate a learned hypothesis ranker on disjoint synthetic universes without touching FTX1 BLIND.

**Architecture:** Preserve the P0 raw-text quarantine and typed contracts. Add rule AST + hypothesis beam + prediction/revision + temporal/conflict/counterfactual semantics, then add an independent synthetic meta-training pipeline whose learned ranker proposes/ranks typed hypotheses but never bypasses the symbolic executor or epistemic controller.

**Tech Stack:** Python >=3.11, stdlib dataclasses/enums/typing/random/hashlib/json, pytest >=8, torch >=2.2 already declared by the repository.

**Spec:** `docs/superpowers/specs/2026-09-18-nexus-unified-v3-p01-hypothesis-engine-training-design.md`

## Global Constraints

- All 16 existing P0 tests remain unchanged and must pass.
- FTX1 BLIND corpus, gold, generator and metadata stay sealed.
- META-OOS is never used for gradient updates, threshold tuning, model selection, or early stopping.
- Learned components emit typed proposals/rankings only; final reasoning remains symbolic + epistemic.
- No raw prompt/history/document text enters hypothesis search, execution, epistemic consensus, or counterfactual execution.
- Every new behavior starts with a failing test.
- Operator/entity names do not influence rule complexity or structural fingerprints.
- Training reports separate META-TRAIN, META-DEV and META-OOS.

---

### Task 1: Backward-compatible P0.1 contracts

**Files:**
- Modify: `src/nexus_gllm/unified_v3/contracts.py`
- Test: `tests/unified_v3/test_p01_contracts.py`

**Interfaces:**
- Produces enums `HypothesisStatus`, `FactLifecycle`, `PredictionOutcome`, `ConflictResolution`, `InterventionKind`.
- Produces dataclasses `RuleClause`, `HypothesisState`, `HypothesisBeam`, `Prediction`, `FactVersion`, `ConflictSet`, `Intervention`, `CounterfactualComparison`.
- Extends `TaskOpcode` without changing existing `QUERY_RELATION`.

- [ ] Write failing tests asserting old P0 constructors still work and new enums/dataclasses exist.
- [ ] Run `pytest tests/unified_v3/test_p01_contracts.py -q` and verify RED.
- [ ] Implement frozen typed contracts with defaults that preserve P0 call sites.
- [ ] Run the test plus all old P0 tests and verify GREEN.

### Task 2: Typed rule algebra

**Files:**
- Create: `src/nexus_gllm/unified_v3/rule_algebra.py`
- Modify: `src/nexus_gllm/unified_v3/rule_induction.py`
- Test: `tests/unified_v3/test_rule_algebra.py`

**Interfaces:**
- Produces `RuleFamily`, `AtomPattern`, `Variable`, `RuleCondition`, `RuleBlocker`.
- Produces `candidate_rule_programs(demonstrations) -> tuple[RuleProgram, ...]`.
- Keeps `RuleInducer.induce()` compatible for P0 while adding `RuleInducer.candidates()`.

- [ ] Write RED tests for symmetric, inverse, transitive, heterogeneous composition, conditional and blocked rules.
- [ ] Add rename-invariance structural fingerprint tests.
- [ ] Implement minimal rule AST and candidate generation.
- [ ] Verify `pytest tests/unified_v3/test_rule_algebra.py tests/unified_v3/test_rule_induction.py -q`.

### Task 3: Competing hypothesis beam

**Files:**
- Create: `src/nexus_gllm/unified_v3/hypotheses.py`
- Create: `src/nexus_gllm/unified_v3/hypothesis_search.py`
- Test: `tests/unified_v3/test_hypothesis_beam.py`

**Interfaces:**
- Produces `HypothesisSearch.seed(worlds, rule_programs) -> HypothesisBeam`.
- Produces `HypothesisSearch.rescore(beam, observations, predictions=()) -> HypothesisBeam`.
- Structural dedupe ignores entity/operator names and favors lower complexity on tied explanatory score.

- [ ] Write RED test where two hypotheses survive an underdetermined episode.
- [ ] Write RED test where discriminating evidence reverses ranking.
- [ ] Write RED test proving renames preserve rank order.
- [ ] Implement bounded beam width 8, score decomposition and lineage.
- [ ] Verify focused tests plus P0 regressions.

### Task 4: Prediction ledger and revision

**Files:**
- Create: `src/nexus_gllm/unified_v3/prediction.py`
- Test: `tests/unified_v3/test_prediction_revision.py`

**Interfaces:**
- Produces `PredictionLedger.emit(beam) -> tuple[Prediction, ...]`.
- Produces `PredictionLedger.resolve(predictions, observations) -> tuple[Prediction, ...]`.
- Produces score deltas for confirmed/refuted predictions.

- [ ] RED: confirmed prediction improves rank.
- [ ] RED: refuted prediction lowers rank without silently deleting the hypothesis.
- [ ] Implement ledger and integrate with hypothesis rescoring.
- [ ] GREEN focused suite.

### Task 5: Temporal revision and conflicts

**Files:**
- Create: `src/nexus_gllm/unified_v3/temporal.py`
- Create: `src/nexus_gllm/unified_v3/conflicts.py`
- Test: `tests/unified_v3/test_temporal_conflicts.py`

**Interfaces:**
- Produces immutable revision ledger with `ACTIVE/SUPERSEDED/RETRACTED/TEMPORARY/CONDITIONAL`.
- Produces `current_fact(...)`, `historical_fact(...)`, and `ConflictEngine.resolve(...)`.

- [ ] RED: correction changes current state while history remains queryable.
- [ ] RED: positive and negative support forms `CONFLICTED` instead of last-write-wins.
- [ ] Implement revision/conflict engine.
- [ ] GREEN focused suite.

### Task 6: Counterfactual worlds

**Files:**
- Create: `src/nexus_gllm/unified_v3/counterfactual.py`
- Test: `tests/unified_v3/test_counterfactual.py`

**Interfaces:**
- Produces `CounterfactualEngine.apply(world, interventions) -> WorldHypothesis`.
- Produces `compare(actual_result, counterfactual_result, ...) -> CounterfactualComparison`.

- [ ] RED: remove one support edge only from cloned world.
- [ ] RED: actual world fingerprint remains unchanged.
- [ ] Implement typed ADD/REMOVE/FLIP/SET_STATE/BLOCK_RULE/ENABLE_RULE interventions.
- [ ] GREEN focused suite.

### Task 7: Rich task IR + executor extensions

**Files:**
- Modify: `src/nexus_gllm/unified_v3/task_induction.py`
- Modify: `src/nexus_gllm/unified_v3/executor.py`
- Test: `tests/unified_v3/test_rich_tasks_executor.py`

**Interfaces:**
- Supports `SELECT_ENTITY, EXTRACT_SET, ORDER_TUPLE, EPISTEMIC_STATUS, FIND_PROOF, FIND_MINIMAL_PROOF, COMPARE_WORLDS, COUNTERFACTUAL_QUERY, CURRENT_STATE, HISTORICAL_STATE`.
- Executor applies rule AST up to bounded depth and returns typed provenance.

- [ ] RED tests for inverse, symmetry, heterogeneous composition, blocker, minimal proof and current/historical state.
- [ ] Implement typed forward chaining with explicit negative facts and temporal filters.
- [ ] GREEN focused suite + all P0 tests.

### Task 8: Beam epistemics + Generalization Governor v2

**Files:**
- Modify: `src/nexus_gllm/unified_v3/epistemic.py`
- Modify: `src/nexus_gllm/unified_v3/generalization.py`
- Test: `tests/unified_v3/test_beam_epistemics_generalization.py`

**Interfaces:**
- Produces weighted `support_mass/contradiction_mass/unresolved_mass`.
- Adds hypothesis-shape stability and intervention sensitivity.

- [ ] RED: 51/49 fragmented support remains unresolved under conservative threshold.
- [ ] RED: aligned high-mass hypotheses prove conclusion.
- [ ] RED: renamed universe preserves hypothesis stability.
- [ ] Implement consensus and stability metrics.
- [ ] GREEN focused suite.

### Task 9: P0.1 runtime integration

**Files:**
- Modify: `src/nexus_gllm/unified_v3/runtime.py`
- Test: `tests/unified_v3/test_p01_runtime.py`

**Interfaces:**
- Adds `respond_hypothesis_episode(...)` while preserving existing `respond()`.
- Trace includes seed, predict, rescore, prune/fork, execute, counterfactual and consensus events.

- [ ] RED full episode: underdetermined -> discriminate -> rerank -> execute -> counterfactual -> consensus.
- [ ] RED renamed-universe twin with structurally equivalent reasoning.
- [ ] Implement orchestration.
- [ ] Run all `tests/unified_v3`.

### Task 10: Synthetic universe generator

**Files:**
- Create package: `training/v3_meta/`
- Create: `universe.py, rule_sampler.py, tasks.py, dataset.py, scorer.py`
- Test: `tests/v3_meta/test_generator.py`

**Interfaces:**
- Produces deterministic `SyntheticUniverseGenerator(family, seed)`.
- Produces disjoint META-TRAIN A / META-DEV B / META-OOS C.
- Runtime-visible records omit family/split/gold metadata.

- [ ] RED separation tests for namespaces, rule compositions and renderer families.
- [ ] RED gold-consistency tests against symbolic executor.
- [ ] Implement generator/scorer.
- [ ] GREEN generator suite.

### Task 11: Learned hypothesis ranker and anti-shortcut baselines

**Files:**
- Create: `training/v3_meta/ranker.py`
- Create: `training/v3_meta/baselines.py`
- Test: `tests/v3_meta/test_ranker.py`

**Interfaces:**
- Ranker consumes structural numeric features only.
- Baselines: frequency, operator-token identity, always-transitive/simple-prior.
- Feature extractor explicitly excludes split/family/case/gold/renderer IDs.

- [ ] RED feature-leak test.
- [ ] RED smoke-learning test on synthetic hypotheses.
- [ ] Implement a small PyTorch MLP ranker and baselines.
- [ ] GREEN ranker tests.

### Task 12: Training + META-OOS evaluation

**Files:**
- Create: `training/v3_meta/train.py`
- Create: `training/v3_meta/evaluate.py`
- Create: `training/v3_meta/config.py`
- Create output: `artifacts/v3_meta/`
- Test: `tests/v3_meta/test_training_smoke.py`

**Interfaces:**
- CLI supports `--train-episodes --dev-episodes --oos-episodes --seed --epochs`.
- Persists checkpoint, config, corpus manifest and metrics JSON.
- Model selection uses META-DEV only; OOS runs after checkpoint choice.

- [ ] RED deterministic smoke-training test.
- [ ] Implement seeded train/eval loop.
- [ ] Run 10k/1k/1k smoke if compute permits; otherwise run the largest completed bounded corpus and label it accurately.
- [ ] If smoke is stable and runtime permits, run target 50k/5k/5k.
- [ ] Evaluate baselines and ranker on META-OOS.
- [ ] Persist hashes and metrics.

### Task 13: Verification checkpoint

**Files:**
- Create: `docs/results/2026-09-18-nexus-unified-v3-p01-training-report.md`

- [ ] Run all P0/P0.1 tests.
- [ ] Run all `tests/v3_meta`.
- [ ] Run compileall on `src/nexus_gllm/unified_v3 training/v3_meta`.
- [ ] Run forbidden-feature and FTX1 anti-leak scans.
- [ ] Record exact training corpus sizes, train/dev/OOS metrics, baseline comparisons, hashes and known limits.
- [ ] Commit only after fresh verification evidence.
