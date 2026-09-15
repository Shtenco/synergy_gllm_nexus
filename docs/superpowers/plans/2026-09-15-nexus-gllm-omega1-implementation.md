# NEXUS GLLM Ω-1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable graph-native language/cognition prototype with no pretrained LLM dependency: Russian text -> dynamic hypergraph -> graph reasoning -> AnswerGraph -> Russian text.

**Architecture:** A deterministic symbolic shell (GraphScript, graph store, compiler, rules, persistence, fallback realizer) surrounds a trainable PyTorch recurrent graph core and an experimental graph-conditioned GRU realizer. Neural structural proposals are policy-gated; persistent memory mutations remain deterministic and auditable.

**Tech Stack:** Python 3.11+, PyTorch 2.2+, pytest 8+, standard library only beyond PyTorch/pytest.

**Spec:** `docs/superpowers/specs/2026-09-15-nexus-gllm-omega1-design.md`

## Global Constraints

- No pretrained LLM is a runtime dependency.
- No Transformers, PyG, DGL, NetworkX, or external LLM API is mandatory.
- GraphScript never executes dynamic code.
- Canonical persistence is JSON; untrusted pickle loading is forbidden.
- Tests use deterministic IDs/seeds.
- Neural logits never mutate persistent graph memory without deterministic validation.
- Benchmark claims must name exact split/config/seed.

---

### Task 1: Project contract, schema, and CI

**Files:**
- Create: `pyproject.toml`
- Create: `.github/workflows/ci.yml`
- Create: `src/nexus_gllm/__init__.py`
- Create: `tests/test_schema.py`
- Create after RED: `src/nexus_gllm/schema.py`

**Interfaces:**
- Produces: `NodeType`, `MutationOp`, `GraphCard`, `TypedHyperEdge`, `GraphUpdate`, `AnswerGraph`, `GLLMResponse`.

- [ ] **Step 1: Write failing schema tests** asserting enum values, confidence validation, immutable identifiers, and AnswerGraph support IDs.
- [ ] **Step 2: Run `pytest tests/test_schema.py -v`** and confirm import failure because `schema.py` does not exist.
- [ ] **Step 3: Implement dataclasses/enums with explicit validation in `__post_init__`**.
- [ ] **Step 4: Run schema tests and full test suite**.
- [ ] **Step 5: Commit** `feat: define GLLM graph contracts`.

### Task 2: Dynamic typed hypergraph and deterministic persistence

**Files:**
- Create: `tests/test_graph.py`
- Create: `tests/test_persistence.py`
- Create after RED: `src/nexus_gllm/graph.py`
- Create after RED: `src/nexus_gllm/persistence.py`

**Interfaces:**
- Consumes: schema dataclasses.
- Produces: `DynamicHyperGraph`, `GraphMutationError`, `save_graph_json`, `load_graph_json`.

- [ ] **Step 1: Write failing tests** for create/link/unlink/retract/update, duplicate-ID rejection, deterministic JSON round-trip, and mutation log version increments.
- [ ] **Step 2: Run focused tests and confirm RED**.
- [ ] **Step 3: Implement minimal graph store and JSON persistence**.
- [ ] **Step 4: Run focused/full tests**.
- [ ] **Step 5: Commit** `feat: add dynamic hypergraph and persistence`.

### Task 3: GraphScript parser/formatter

**Files:**
- Create: `tests/test_graphscript.py`
- Create after RED: `src/nexus_gllm/graphscript.py`

**Interfaces:**
- Produces: `parse_graphscript(text) -> GraphScriptDocument`, `format_graphscript(document) -> str`.

- [ ] **Step 1: Write failing tests** for NODE, EDGE, QUERY, ANSWER, confidence, invalid syntax, and parse/format/parse equality.
- [ ] **Step 2: Run tests and confirm RED**.
- [ ] **Step 3: Implement strict line-oriented parser without eval**.
- [ ] **Step 4: Run tests/full suite**.
- [ ] **Step 5: Commit** `feat: add safe GraphScript interchange language`.

### Task 4: Russian graph compiler

**Files:**
- Create: `tests/test_compiler_ru.py`
- Create after RED: `src/nexus_gllm/compiler_ru.py`

**Interfaces:**
- Produces: `RussianGraphCompiler.compile_statement`, `.compile_question`, normalized relation names `is_a`, `older_than`, `located_in`, `owned_by`.

- [ ] **Step 1: Write failing tests** for supported Russian constructions and unseen proper names.
- [ ] **Step 2: Run tests and confirm RED**.
- [ ] **Step 3: Implement deterministic tokenizer/pattern compiler with stable hashed IDs**.
- [ ] **Step 4: Run tests/full suite**.
- [ ] **Step 5: Commit** `feat: compile Russian micro-world text into graph`.

### Task 5: Rule engine and answer selection

**Files:**
- Create: `tests/test_rules.py`
- Create after RED: `src/nexus_gllm/rules.py`
- Create after RED: `src/nexus_gllm/answer.py`

**Interfaces:**
- Produces: `RuleEngine.infer(graph)`, `AnswerResolver.resolve(graph, query)`.

- [ ] **Step 1: Write failing tests** for transitive `older_than`, location/ownership lookup, provenance, duplicate derived-edge suppression, and unknown-answer abstention.
- [ ] **Step 2: Run tests and confirm RED**.
- [ ] **Step 3: Implement rule inference and AnswerGraph creation**.
- [ ] **Step 4: Run tests/full suite**.
- [ ] **Step 5: Commit** `feat: add graph rule inference and answer graphs`.

### Task 6: Active workspace retrieval

**Files:**
- Create: `tests/test_workspace.py`
- Create after RED: `src/nexus_gllm/workspace.py`

**Interfaces:**
- Produces: `ActiveWorkspace`, `WorkspaceRetriever.retrieve(graph, seeds, limit)`.

- [ ] **Step 1: Write failing tests** for bounded size, seed preservation, neighborhood expansion, activation ranking, and deterministic tie-breaking.
- [ ] **Step 2: Run tests and confirm RED**.
- [ ] **Step 3: Implement retrieval and activation spreading**.
- [ ] **Step 4: Run tests/full suite**.
- [ ] **Step 5: Commit** `feat: add bounded active graph workspace`.

### Task 7: Recurrent graph neural core

**Files:**
- Create: `tests/test_recurrent.py`
- Create after RED: `src/nexus_gllm/recurrent.py`

**Interfaces:**
- Produces: `GraphTensorBatch`, `GraphRecurrentCore.forward`, operation logits over `NOOP/ACTIVATE/SUPPRESS/LINK/RETRACT/ANSWER`.

- [ ] **Step 1: Write failing tests** for tensor shapes, deterministic seeded forward pass, gradient flow, empty-edge handling, and bounded recurrent steps.
- [ ] **Step 2: Run tests and confirm RED**.
- [ ] **Step 3: Implement plain-PyTorch typed message passing + GRUCell updates + global broadcast + op head**.
- [ ] **Step 4: Run tests/full suite**.
- [ ] **Step 5: Commit** `feat: add recurrent graph cognition core`.

### Task 8: Russian realization

**Files:**
- Create: `tests/test_realizer_ru.py`
- Create after RED: `src/nexus_gllm/realizer_ru.py`

**Interfaces:**
- Produces: `DeterministicRussianRealizer.realize(AnswerGraph, graph) -> str`, `NeuralGraphRealizer`.

- [ ] **Step 1: Write failing tests** that exact supported answers are preserved in Russian and neural realizer has correct tensor/gradient behavior.
- [ ] **Step 2: Run tests and confirm RED**.
- [ ] **Step 3: Implement deterministic templates plus small GRU graph-conditioned decoder skeleton**.
- [ ] **Step 4: Run tests/full suite**.
- [ ] **Step 5: Commit** `feat: add graph-to-Russian realization`.

### Task 9: End-to-end NexusGLLM

**Files:**
- Create: `tests/test_end_to_end.py`
- Create after RED: `src/nexus_gllm/model.py`

**Interfaces:**
- Produces: `NexusGLLM.learn`, `.ask`, `.save`, `.load`.

- [ ] **Step 1: Write failing E2E tests** for learning two age facts, inferring oldest via transitivity, location, possession, unknown abstention, and persistence reload.
- [ ] **Step 2: Run tests and confirm RED**.
- [ ] **Step 3: Implement orchestrator wiring compiler, graph, rules, workspace, AnswerGraph, realizer**.
- [ ] **Step 4: Run tests/full suite**.
- [ ] **Step 5: Commit** `feat: deliver graph-native NEXUS GLLM runtime`.

### Task 10: Synthetic dataset, trainer, and benchmark harness

**Files:**
- Create: `tests/test_dataset.py`
- Create: `training/__init__.py`
- Create after RED: `training/dataset.py`
- Create after RED: `training/generate_synthetic.py`
- Create after RED: `training/train_core.py`
- Create: `benchmarks/freeze_manifest.py`
- Create: `benchmarks/run_benchmark.py`

**Interfaces:**
- Produces deterministic JSONL generation, train/dev/blind manifests, a recurrent-core training CLI, and raw benchmark JSON output.

- [ ] **Step 1: Write failing tests** for deterministic seeded corpus generation, disjoint entity sets, split manifest hashing, and dataset decoding.
- [ ] **Step 2: Run tests and confirm RED**.
- [ ] **Step 3: Implement dataset/generator/trainer/benchmark harness**.
- [ ] **Step 4: Run tests/full suite and a 2-step smoke train**.
- [ ] **Step 5: Commit** `feat: add reproducible GLLM training and benchmark pipeline`.

### Task 11: Documentation and release verification

**Files:**
- Modify: `README.md`
- Create: `ARCHITECTURE.md`
- Create: `PROVENANCE.md`

**Interfaces:**
- Documents exact runtime scope, commands, limitations, and no-LLM invariant.

- [ ] **Step 1: Document install, examples, GraphScript, training, benchmark and limitations**.
- [ ] **Step 2: Run `python -m compileall src training benchmarks`**.
- [ ] **Step 3: Run `pytest -q`**.
- [ ] **Step 4: Run E2E demo and benchmark smoke command**.
- [ ] **Step 5: Commit** `docs: document NEXUS GLLM Omega-1`.

### Task 12: Pull request and CI evidence

**Files:** no production changes unless CI exposes a defect.

- [ ] **Step 1: Open PR from `nexus-gllm-omega1-v1` to `main`** with architecture, test and limitation summary.
- [ ] **Step 2: Inspect CI jobs/logs**.
- [ ] **Step 3: Fix any real CI failures with RED/GREEN discipline**.
- [ ] **Step 4: Record final commit SHA and test evidence in PR**.
