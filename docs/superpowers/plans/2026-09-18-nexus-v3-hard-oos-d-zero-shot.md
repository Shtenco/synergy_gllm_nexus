# NEXUS v3 HARD-OOS D Zero-Shot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independent 10,000-episode adversarial HARD-OOS D generator, seal it, and evaluate the frozen P0.1 checkpoint zero-shot without any D-informed update.

**Architecture:** HARD-OOS D lives under `training/v3_hard_oos_d/` and does not import A/B/C generator logic. It generates scorer-side latent AST programs plus runtime-visible observations, exposes a frozen 8-channel compatibility adapter for the existing ranker, evaluates symbolic coverage separately, and persists a sealed manifest before model execution.

**Tech Stack:** Python >=3.11, dataclasses/enums/random/hashlib/json, pytest >=8, torch >=2.2.

**Spec:** `docs/superpowers/specs/2026-09-18-nexus-v3-hard-oos-d-zero-shot-design.md`

## Global Constraints

- Frozen model SHA-256 must equal `95fd54d5036c7dfda0da1b9edbff5b804e6fa7163aab2fec83459075eb3b2c96`.
- D generator MUST NOT import `training.v3_meta.universe`.
- No gradient update, optimizer step, checkpoint mutation, threshold tuning, or D-informed feature change is allowed before the first D report.
- Runtime-visible records exclude stratum, gold AST/topology, expected ranking, proof, target state, and counterfactual gold.
- D is consumed after the first zero-shot report.
- FTX1 BLIND remains unopened.
- Existing 33 P0/P0.1 tests remain regression gates.

---

### Task 1: Independent AST and topology fingerprint

**Files:**
- Create: `training/v3_hard_oos_d/ast.py`
- Test: `tests/v3_hard_oos_d/test_ast.py`

**Interfaces:**
- `NodeKind` enum for ATOM/AND/NOT/IMPLIES/COMPOSE/INVERSE/SYMMETRIC/TEMPORAL_BEFORE/TEMPORAL_AFTER/STATE_GATE/INHIBITOR/EXCEPTION/COUNTERFACTUAL_INTERVENTION.
- Frozen `AstNode(kind, children, arity)`.
- `topology_fingerprint(node) -> str` ignores entity/operator tokens.

- [ ] Write RED tests showing token renames preserve topology fingerprint and distinct nesting changes it.
- [ ] Run focused test and verify failure because package is absent.
- [ ] Implement AST/fingerprint.
- [ ] Run focused GREEN.

### Task 2: Episode contracts and six independent strata

**Files:**
- Create: `training/v3_hard_oos_d/generator.py`
- Create: `training/v3_hard_oos_d/strata.py`
- Test: `tests/v3_hard_oos_d/test_generator.py`

**Interfaces:**
- `HardDEpisode` stores scorer-only gold plus `runtime_record()`.
- `HardOOSDGenerator(seed).generate() -> tuple[HardDEpisode,...]`.
- Exact allocation: 2000/1500/1500/1500/1500/2000.

- [ ] RED exact-count test.
- [ ] RED runtime-field deny-list test.
- [ ] RED import-independence scan.
- [ ] Implement deterministic stratum generation with opaque episode IDs.
- [ ] GREEN.

### Task 3: Novel AST/disjoint topology inventory

**Files:**
- Create: `training/v3_hard_oos_d/programs.py`
- Test: `tests/v3_hard_oos_d/test_topology_disjointness.py`

**Interfaces:**
- Program templates include heterogeneous composition, 3-antecedent conjunction, condition+inhibitor, temporal consequence, composition+inhibition, exception override, hidden intermediate and counterfactual-intermediate.

- [ ] RED assert D inventory excludes A/B/C singleton-family topology set.
- [ ] Implement independent templates and inventory.
- [ ] GREEN.

### Task 4: Partial/noisy, distractor and ambiguity mechanics

**Files:**
- Create: `training/v3_hard_oos_d/distractors.py`
- Create: `training/v3_hard_oos_d/bindings.py`
- Test: `tests/v3_hard_oos_d/test_adversarial_mechanics.py`

- [ ] RED: partial/noisy ratios remain within spec.
- [ ] RED: some ambiguity episodes target UNRESOLVED.
- [ ] RED: rename twins preserve gold topology.
- [ ] Implement deterministic corruption, adversarial distractors, ambiguity and rename transforms.
- [ ] GREEN.

### Task 5: Temporal/inhibitor and counterfactual traps

**Files:**
- Create: `training/v3_hard_oos_d/temporal.py`
- Create: `training/v3_hard_oos_d/counterfactual.py`
- Test: `tests/v3_hard_oos_d/test_temporal_counterfactual.py`

- [ ] RED necessary-support, redundant-support, blocker-flip and irrelevant-intervention cases.
- [ ] RED actual-world immutability.
- [ ] Implement scorer-side trap generation.
- [ ] GREEN.

### Task 6: Frozen compatibility adapter and baselines

**Files:**
- Create: `training/v3_hard_oos_d/adapter.py`
- Create: `training/v3_hard_oos_d/baselines.py`
- Test: `tests/v3_hard_oos_d/test_adapter_baselines.py`

**Interfaces:**
- `compat_features(episode, candidate) -> list[float]` returns exactly 8 frozen channels.
- Baselines: random, simplicity, explained, contradiction, nearest-known, always-transitive.

- [ ] RED feature-width and gold-field isolation.
- [ ] RED ensure evaluator module contains no optimizer/fit call.
- [ ] Implement adapter/baselines.
- [ ] GREEN.

### Task 7: Scorer and D metrics

**Files:**
- Create: `training/v3_hard_oos_d/scorer.py`
- Test: `tests/v3_hard_oos_d/test_scorer.py`

**Interfaces:**
- Aggregate and per-stratum metrics: answer, AST exact/partial, ranking, prediction, counterfactual, temporal, inhibitor, binding, abstention, rename invariance, hypothesis stability, theory revision, ECE, representation failure.

- [ ] RED metric denominator includes representation failures.
- [ ] RED per-stratum output includes all six strata.
- [ ] Implement scorer.
- [ ] GREEN.

### Task 8: Seal corpus before evaluation

**Files:**
- Create: `training/v3_hard_oos_d/seal.py`
- Output: `artifacts/v3_hard_oos_d/manifest.json`, `corpus_summary.json`, `topology_inventory.json`
- Test: `tests/v3_hard_oos_d/test_seal.py`

- [ ] RED frozen checkpoint hash mismatch must abort.
- [ ] Generate 10,000 episodes.
- [ ] Compute canonical corpus hash from scorer-side episode serialization.
- [ ] Persist manifest with source/model/adapter/scorer/config hashes.
- [ ] Mark manifest `sealed_before_evaluation=true`.
- [ ] GREEN.

### Task 9: Frozen zero-shot evaluator

**Files:**
- Create: `training/v3_hard_oos_d/evaluate.py`
- Test: `tests/v3_hard_oos_d/test_zero_shot.py`

- [ ] RED evaluator rejects unsealed manifest.
- [ ] RED evaluator rejects checkpoint hash mismatch.
- [ ] Load frozen P0.1 model with no optimizer and no gradient.
- [ ] Evaluate compatibility ranking + baselines.
- [ ] Evaluate symbolic representability/coverage separately.
- [ ] Persist `zero_shot_metrics.json`, `baseline_metrics.json`.
- [ ] GREEN.

### Task 10: One-shot 10k execution and verification report

**Files:**
- Create: `docs/results/2026-09-18-nexus-v3-hard-oos-d-zero-shot-report.md`

- [ ] Run existing `tests/unified_v3 tests/v3_meta`.
- [ ] Run all `tests/v3_hard_oos_d`.
- [ ] Compile `training/v3_hard_oos_d`.
- [ ] Run anti-leak/import/update scans.
- [ ] Verify frozen model hash.
- [ ] Seal D corpus.
- [ ] Run exactly one zero-shot evaluation.
- [ ] Record all metrics and baselines by stratum.
- [ ] Mark D consumed.
- [ ] Commit implementation, artifacts and report.
