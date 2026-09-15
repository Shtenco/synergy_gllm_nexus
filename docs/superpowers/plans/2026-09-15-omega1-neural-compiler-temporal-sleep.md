# NEXUS GLLM Ω-1.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a trainable Russian→Graph compiler, temporal/causal event reasoning, and deterministic sleep/consolidation to Ω-1 without introducing a pretrained LLM into runtime.

**Architecture:** Russian text is encoded by a character-native BiGRU that predicts a structured `NeuralParseProposal`; validation gates all persistent mutations. Events live as typed graph nodes with `before`/`causes` relations and deterministic closure/cycle checks. Offline `GraphConsolidator` merges duplicates, accumulates evidence, resolves exclusive world-state conflicts, and promotes stable semantic facts.

**Tech Stack:** Python >=3.11, PyTorch >=2.2, dataclasses, pytest >=8, JSON/JSONL.

**Spec:** `docs/superpowers/specs/2026-09-15-omega1-neural-compiler-temporal-sleep-design.md`

## Global Constraints

- No pretrained LLM dependency in canonical runtime.
- Raw neural proposals never mutate persistent memory without validation.
- Existing deterministic compiler remains verifier/fallback.
- Blind templates and entity/event surfaces are disjoint from train/dev and frozen before selection.
- No physical deletion during Ω-1.1 consolidation.
- Benchmark claims must be tied to exact artifacts and hashes.

---

### Task 1: Structured neural compiler contract

**Files:**
- Create: `src/nexus_gllm/compiler_proposal.py`
- Test: `tests/test_neural_compiler.py`

**Interfaces:**
- Produces: `NeuralParseProposal`, `ProposalValidator`, `ValidationResult`.

- [ ] **Step 1: Write failing tests** for span bounds, relation allow-list, confidence threshold, self-loop rejection, and abstention.
- [ ] **Step 2: Run** `pytest tests/test_neural_compiler.py -q`; expected import/behavior failures.
- [ ] **Step 3: Implement** immutable proposal/validation dataclasses and deterministic validator.
- [ ] **Step 4: Run** `pytest tests/test_neural_compiler.py -q`; expected pass.
- [ ] **Step 5: Commit** `feat: add neural compiler proposal contract`.

### Task 2: Character-native Russian compiler model

**Files:**
- Create: `src/nexus_gllm/compiler_neural.py`
- Extend: `tests/test_neural_compiler.py`

**Interfaces:**
- Consumes: `NeuralParseProposal`.
- Produces: `CompilerCharVocab`, `NeuralRussianGraphCompiler.forward()`, `predict()` and checkpoint save/load.

- [ ] **Step 1: Add failing tests** for forward tensor shapes, gradients, bounded span decoding, checkpoint round-trip.
- [ ] **Step 2: Run** focused tests and confirm RED.
- [ ] **Step 3: Implement** char embedding + BiGRU + relation/span/confidence heads and deterministic decoding.
- [ ] **Step 4: Re-run** focused tests and confirm GREEN.
- [ ] **Step 5: Commit** `feat: add neural Russian graph compiler`.

### Task 3: Temporal and causal event graph

**Files:**
- Create: `src/nexus_gllm/temporal.py`
- Test: `tests/test_temporal.py`

**Interfaces:**
- Produces: `EventGraphReasoner`, `TemporalQueryResult`, event creation helpers.

- [ ] **Step 1: Add failing tests** for `before` closure, causal ancestry, reverse `after`, cycle rejection, and ignoring retracted edges.
- [ ] **Step 2: Run** `pytest tests/test_temporal.py -q`; confirm RED.
- [ ] **Step 3: Implement** event relation helpers, closure traversal and strict DAG validation.
- [ ] **Step 4: Re-run** focused tests; confirm GREEN.
- [ ] **Step 5: Commit** `feat: add temporal causal event graph`.

### Task 4: Deterministic Russian event bridge

**Files:**
- Modify: `src/nexus_gllm/compiler_ru.py`
- Extend: `tests/test_temporal.py`

**Interfaces:**
- Consumes: `EventGraphReasoner` conventions.
- Produces supported fixtures for `Сначала A, потом B`, `A, поэтому B`, `После A произошло B` and temporal/causal questions.

- [ ] **Step 1: Add failing fixture tests** for three statement forms and two query forms.
- [ ] **Step 2: Run** focused tests; confirm RED.
- [ ] **Step 3: Extend** deterministic compiler without broad free-form claims.
- [ ] **Step 4: Re-run** focused tests; confirm GREEN.
- [ ] **Step 5: Commit** `feat: compile Russian temporal causal fixtures`.

### Task 5: Sleep/consolidation engine

**Files:**
- Create: `src/nexus_gllm/consolidation.py`
- Test: `tests/test_consolidation.py`

**Interfaces:**
- Produces: `GraphConsolidator.run(graph) -> ConsolidationReport`.

- [ ] **Step 1: Add failing tests** for duplicate node merge, edge evidence accumulation using `1-Π(1-c_i)`, exclusive-relation cleanup, semantic promotion, and protected-fact retention.
- [ ] **Step 2: Run** focused tests; confirm RED.
- [ ] **Step 3: Implement** deterministic five-phase consolidation with rewiring and no deletion.
- [ ] **Step 4: Re-run** focused tests; confirm GREEN.
- [ ] **Step 5: Commit** `feat: add graph sleep consolidation`.

### Task 6: Compiler corpus and trainer

**Files:**
- Create: `training/generate_compiler_corpus.py`
- Create: `training/train_compiler.py`
- Test: `tests/test_compiler_training.py`

**Interfaces:**
- Produces JSONL with `compiler_target`, template hashes, split provenance; trainer outputs checkpoint with config/vocabs/manifest hash/state dict.

- [ ] **Step 1: Add failing tests** for split/template disjointness, target span validity, finite multitask loss, checkpoint metadata.
- [ ] **Step 2: Run** focused tests; confirm RED.
- [ ] **Step 3: Implement** corpus generator and multitask CE/BCE trainer with span losses omitted for abstain.
- [ ] **Step 4: Re-run** focused tests; confirm GREEN.
- [ ] **Step 5: Commit** `feat: train neural Russian graph compiler`.

### Task 7: Runtime integration

**Files:**
- Modify: `src/nexus_gllm/model.py`
- Test: `tests/test_neural_compiler_runtime.py`

**Interfaces:**
- Produces: `load_compiler_checkpoint()` and neural-first validated `learn()` path with deterministic fallback.

- [ ] **Step 1: Add failing tests** proving accepted neural proposal mutates graph, rejected proposal falls back, and incompatible checkpoints are rejected.
- [ ] **Step 2: Run** focused tests; confirm RED.
- [ ] **Step 3: Integrate** compiler checkpoint and validator without granting raw neural authority.
- [ ] **Step 4: Re-run** focused tests; confirm GREEN.
- [ ] **Step 5: Commit** `feat: integrate neural compiler into NexusGLLM`.

### Task 8: Frozen benchmarks and documentation

**Files:**
- Create: `benchmarks/run_compiler_benchmark.py`
- Create: `benchmarks/run_temporal_benchmark.py`
- Create: `benchmarks/run_consolidation_benchmark.py`
- Modify: `README.md`, `ARCHITECTURE.md`, `PROVENANCE.md`

**Interfaces:**
- Produces per-task JSON metrics and hashable raw outputs.

- [ ] **Step 1: Add benchmark smoke tests** for exact-match metrics, cycle/retraction cases and consolidation invariants.
- [ ] **Step 2: Run** benchmark smoke tests; confirm RED where runners are missing.
- [ ] **Step 3: Implement** runners and documentation with no unverified quality claims.
- [ ] **Step 4: Run** `pytest -q` and `python -m compileall src training benchmarks`; record exact result.
- [ ] **Step 5: Commit** `bench: add Omega-1.1 frozen evaluation harness`.
