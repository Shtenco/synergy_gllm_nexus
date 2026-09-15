# NEXUS GLLM Ω-1.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit evidence-backed belief revision, contradiction handling, source reliability, zero-gradient fact acquisition, gated continual learning, and a reproducible 100K corpus to Ω-1.1.

**Architecture:** Observations compile into structured propositions, become immutable evidence, update BeliefGraph posteriors, and only active beliefs project into semantic graph state. Neural weights update only during explicit sleep-training with protected replay and promotion/rollback gates.

**Tech Stack:** Python 3.11+, PyTorch >=2.2, standard library dataclasses/json/math/hashlib/random, pytest >=8.

**Spec:** `docs/superpowers/specs/2026-09-15-omega1-belief-continual-design.md`

## Global Constraints

- No pretrained LLM dependency in canonical runtime.
- Evidence history is non-destructive and auditable.
- Ordinary factual acquisition must require zero gradient steps.
- Neural proposals cannot directly mutate protected belief/semantic state.
- Train/dev/blind splits must use disjoint entity/source/template/order patterns.
- Stage A is exactly 100,000 train situations; Stage B/C/D are gated.
- Invalid accepted memory mutation rate target is 0%.

---

### Task 1: Evidence ledger and source reliability

**Files:**
- Create: `src/nexus_gllm/evidence.py`
- Create: `src/nexus_gllm/source_reliability.py`
- Test: `tests/test_source_reliability.py`

**Interfaces:**
- Produces: `EvidenceRecord`, `EvidenceLedger`, `SourceReliability`, `SourceRegistry`.

- [ ] Write failing tests for immutable evidence IDs, duplicate rejection, Beta reliability updates, and reliability bounds.
- [ ] Run `pytest tests/test_source_reliability.py -q` and verify RED.
- [ ] Implement deterministic evidence hashing and source updates.
- [ ] Re-run targeted tests and verify GREEN.
- [ ] Commit.

### Task 2: BeliefGraph revision engine

**Files:**
- Create: `src/nexus_gllm/belief.py`
- Test: `tests/test_belief_graph.py`

**Interfaces:**
- Consumes: `EvidenceLedger`, `SourceRegistry`.
- Produces: `BeliefKey`, `BeliefSnapshot`, `BeliefUpdate`, `BeliefGraph.observe()` and query APIs.

- [ ] Write failing tests covering support-only active belief, attack-only retraction, mixed disputed state, Brier-safe posterior bounds, and zero-gradient fact acquisition metadata.
- [ ] Run targeted tests and verify RED.
- [ ] Implement log-odds evidence accumulation and status thresholds.
- [ ] Re-run targeted tests and verify GREEN.
- [ ] Commit.

### Task 3: Contradiction engine

**Files:**
- Create: `src/nexus_gllm/contradiction.py`
- Test: `tests/test_contradiction.py`

**Interfaces:**
- Consumes: `BeliefKey`, `BeliefGraph`, existing temporal graph.
- Produces: `ContradictionSet`, `ContradictionEngine.detect()`.

- [ ] Write failing tests for `owned_by`/`located_in` functional conflicts, direct polarity conflict and strict temporal-cycle contradiction.
- [ ] Run targeted tests and verify RED.
- [ ] Implement only registered contradiction schemas; no ontology guessing.
- [ ] Re-run tests and verify GREEN.
- [ ] Commit.

### Task 4: Runtime observation and semantic projection

**Files:**
- Modify: `src/nexus_gllm/model.py`
- Modify: `src/nexus_gllm/schema.py`
- Test: `tests/test_belief_runtime.py`

**Interfaces:**
- Produces: `NexusGLLM.observe()`, `NexusGLLM.belief()`, `NexusGLLM.correct_source()`.

- [ ] Write failing tests where conflicting ownership observations remain historically present while only the higher active belief projects to the semantic graph.
- [ ] Run targeted tests and verify RED.
- [ ] Implement observation→evidence→belief→contradiction→projection path.
- [ ] Re-run targeted tests and verify GREEN.
- [ ] Commit.

### Task 5: Replay buffer and continual promotion gate

**Files:**
- Create: `training/replay_buffer.py`
- Create: `src/nexus_gllm/continual.py`
- Test: `tests/test_continual_learning.py`

**Interfaces:**
- Produces: `ReplayItem`, `ReplayBuffer`, `PromotionMetrics`, `PromotionGate`, `ContinualLearningReport`.

- [ ] Write failing tests for deterministic replay sampling, protected quota, promotion on gain/no regression and rollback on protected regression.
- [ ] Run targeted tests and verify RED.
- [ ] Implement deterministic sampling and pure promotion decision logic.
- [ ] Re-run targeted tests and verify GREEN.
- [ ] Commit.

### Task 6: Generate exactly 100K Stage-A corpus

**Files:**
- Create: `training/generate_belief_corpus.py`
- Test: `tests/test_belief_corpus.py`

**Interfaces:**
- Produces JSONL and manifest with exactly 100000 train, 10000 dev, 10000 blind rows.

- [ ] Write failing tests for exact task counts, split sizes, template/source/entity separation and deterministic SHA under fixed seed.
- [ ] Run targeted tests and verify RED.
- [ ] Implement generator with the approved 10-family distribution.
- [ ] Re-run targeted tests and verify GREEN.
- [ ] Generate `data/omega1_2_belief_100k.jsonl` when filesystem runner is available; otherwise expose exact CLI and verify generator via tests.
- [ ] Commit.

### Task 7: Belief and continual benchmarks

**Files:**
- Create: `benchmarks/run_belief_benchmark.py`
- Create: `benchmarks/run_continual_benchmark.py`
- Create: `benchmarks/run_forgetting_benchmark.py`
- Test: `tests/test_belief_benchmarks.py`

**Interfaces:**
- Produces metrics for belief accuracy, Brier score, contradiction P/R, source calibration, new-task gain, retention and forgetting delta.

- [ ] Write failing metric-contract tests with hand-computable fixtures.
- [ ] Run targeted tests and verify RED.
- [ ] Implement benchmark runners and machine-readable JSON output.
- [ ] Re-run targeted tests and verify GREEN.
- [ ] Commit.

### Task 8: Continual trainer scaffold and launch command

**Files:**
- Create: `training/train_continual.py`
- Modify: `README.md`
- Test: `tests/test_train_continual.py`

**Interfaces:**
- Consumes new data and protected replay; trains candidate checkpoint; evaluates candidate; invokes promotion gate.
- Produces promoted/rejected candidate report and rollback-safe checkpoint path.

- [ ] Write failing tests around dry-run candidate evaluation and promotion/rollback path without expensive training.
- [ ] Run targeted tests and verify RED.
- [ ] Implement resumable trainer scaffold using existing native compiler/core checkpoints and replay mixing.
- [ ] Re-run tests and verify GREEN.
- [ ] Add exact 100K generation/training/benchmark commands to README.
- [ ] Attempt available compute launch; record actual output/resource blocker without overclaiming.
- [ ] Commit.

### Task 9: Full verification

- [ ] Run `pytest -q`.
- [ ] Run `python -m compileall src training benchmarks`.
- [ ] Run corpus manifest validation on 100K artifact or generator-produced sample if runtime cannot materialize the full file.
- [ ] Run belief/continual/forgetting smoke benchmarks.
- [ ] Inspect GitHub Actions result and keep PR draft if CI is not green.
- [ ] Update PR with exact evidence and limitations.
