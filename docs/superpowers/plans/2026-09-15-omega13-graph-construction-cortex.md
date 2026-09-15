# NEXUS GLLM Ω-1.3 Graph Construction Cortex Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and locally train a CPU-realistic graph-slot Russian→Graph cortex on the frozen Ω-1.2 Stage A 100K train split, select the checkpoint on dev only, then run one final frozen blind evaluation.

**Architecture:** A train-only character vocabulary and deterministic local morphology features feed a 2-layer bidirectional GRU. Learned SUBJECT, OBJECT, RELATION and GLOBAL graph slots iteratively refine against encoder states. Slot-conditioned valid-span decoding plus a relation head produce a structured `GraphConstructionProposal` which remains behind the existing Ω-1.2 validator contract.

**Tech Stack:** Python 3.11+, PyTorch 2.x CPU, gzip/json, pytest.

**Spec:** `docs/superpowers/specs/2026-09-15-omega13-graph-construction-cortex-design.md`

## Global Constraints

- No pretrained LLM, tokenizer or external embedding model.
- Frozen corpus SHA: `738a8457f38ec8eb75ccc85bd18f713d5df8611e267900f8747de7f78ceebf2a`.
- Train=100,000, dev=10,000, blind=10,000.
- Blind is not used for architecture choice, threshold tuning, early stopping, vocabulary fitting or checkpoint selection.
- Seed=17 for the canonical local run.
- First model must fit CPU-only ~5.8 GiB RAM.
- Promotion to 250K requires blind relation accuracy >40%, strict graph accuracy >0%, invalid accepted proposal rate 0%, and contamination checks passed.

---

### Task 1: Dataset and train-only vocabulary

**Files:**
- Create: `training/graph_cortex_dataset.py`
- Test: `tests/test_graph_cortex_dataset.py`

**Interfaces:**
- Produces `GraphCortexVocab`, `GraphCortexDataset`, `collate_graph_cortex`, and deterministic morphology feature tensors.

- [ ] **Step 1: Write failing tests** verifying train-only vocabulary, exact target span preservation, abstain span masks, max-length padding, and deterministic morphology features.
- [ ] **Step 2: Run** `pytest -q tests/test_graph_cortex_dataset.py` and verify failure due to missing module.
- [ ] **Step 3: Implement dataset/vocabulary** with `<PAD>/<UNK>`, gzip/plain JSONL support, relation vocabulary fixed to seven Stage A classes, and no blind-derived vocabulary state.
- [ ] **Step 4: Run** `pytest -q tests/test_graph_cortex_dataset.py` and require 0 failures.
- [ ] **Step 5: Commit** `feat(omega13): add graph cortex dataset`.

### Task 2: Graph construction schema and valid span decoder

**Files:**
- Create: `src/nexus_gllm/graph_cortex_schema.py`
- Test: `tests/test_graph_cortex.py`

**Interfaces:**
- Produces immutable `GraphNodeProposal`, `GraphEdgeProposal`, `GraphConstructionProposal`, and `decode_valid_span(start_logits, end_logits, length, max_width)`.

- [ ] **Step 1: Write failing tests** for proposal validation and pairwise span decoding where greedy independent argmax would produce an invalid span.
- [ ] **Step 2: Run** `pytest -q tests/test_graph_cortex.py::test_decode_valid_span` and verify RED.
- [ ] **Step 3: Implement schema/decoder** using exhaustive bounded pair scoring over at most 96 positions.
- [ ] **Step 4: Re-run targeted tests** and require PASS.
- [ ] **Step 5: Commit** `feat(omega13): add graph construction proposal schema`.

### Task 3: Slot-based GraphConstructionCortex

**Files:**
- Create: `src/nexus_gllm/graph_cortex.py`
- Extend: `tests/test_graph_cortex.py`

**Interfaces:**
- `GraphConstructionCortex.forward(tokens, mask, morph)` returns relation logits, confidence logit, four slot-conditioned span-logit tensors and final slot states.
- `GraphConstructionCortex.predict(text, vocab, relations)` returns `GraphConstructionProposal`.

- [ ] **Step 1: Add failing tests** for tensor shapes, finite gradients, masked padding logits, abstain prediction path, parameter count under 8M and checkpoint round-trip.
- [ ] **Step 2: Run tests** and verify RED.
- [ ] **Step 3: Implement** char embedding 48, morphology projection 16, 2-layer BiGRU hidden 96/direction, 192-dim learned SUBJECT/OBJECT/RELATION/GLOBAL slots, three recurrent refinement steps with slot-to-encoder attention scores and GRUCell updates.
- [ ] **Step 4: Implement relation head** from relation slot + subject/object/global summaries and confidence head.
- [ ] **Step 5: Run** `pytest -q tests/test_graph_cortex.py` and require 0 failures.
- [ ] **Step 6: Commit** `feat(omega13): add slot graph construction cortex`.

### Task 4: Local trainer and dev checkpoint selection

**Files:**
- Create: `training/train_graph_cortex.py`
- Test: `tests/test_graph_cortex_training.py`

**Interfaces:**
- `train_graph_cortex(...) -> dict` writes a checkpoint containing config, train-only vocab, relations, seed, corpus SHA, selected epoch, dev metrics, thresholds and state dict.

- [ ] **Step 1: Write failing tests** on a tiny synthetic subset for one optimization step, separate loss terms, deterministic seed and checkpoint metadata without blind metrics.
- [ ] **Step 2: Run tests** and verify RED.
- [ ] **Step 3: Implement class-balanced relation CE**, span CE for non-abstain rows, confidence BCE, consistency loss and gradient clipping.
- [ ] **Step 4: Implement dev evaluator** computing relation accuracy, macro-F1, subject/object exact, both spans exact, strict graph exact, abstention precision/recall/F1 and Brier score.
- [ ] **Step 5: Implement early stopping** on dev strict graph accuracy with dev relation accuracy as tie-breaker; never construct a blind DataLoader inside training.
- [ ] **Step 6: Run** `pytest -q tests/test_graph_cortex_training.py` and require 0 failures.
- [ ] **Step 7: Commit** `feat(omega13): add local graph cortex trainer`.

### Task 5: Frozen blind benchmark

**Files:**
- Create: `benchmarks/run_graph_cortex_benchmark.py`
- Test: `tests/test_graph_cortex_benchmark.py`

**Interfaces:**
- Benchmark consumes one frozen checkpoint and one requested split; outputs all metrics plus corpus/checkpoint hashes and promotion-gate fields.

- [ ] **Step 1: Write failing metric-contract test** for exact result keys and promotion calculation.
- [ ] **Step 2: Run targeted test** and verify RED.
- [ ] **Step 3: Implement benchmark** reusing evaluator but refusing train-time modification and recording invalid accepted proposal rate after validator compatibility conversion.
- [ ] **Step 4: Run test** and require PASS.
- [ ] **Step 5: Commit** `feat(omega13): add frozen graph cortex benchmark`.

### Task 6: Local RED→GREEN verification

**Files:** all Ω-1.3 files.

- [ ] **Step 1:** `pytest -q tests/test_graph_cortex_dataset.py tests/test_graph_cortex.py tests/test_graph_cortex_training.py tests/test_graph_cortex_benchmark.py`.
- [ ] **Step 2:** `python -m compileall src training benchmarks`.
- [ ] **Step 3:** Run a 2,000-example diagnostic train/dev experiment to verify loss decreases and checkpoint reload works.
- [ ] **Step 4:** If any verification fails, fix by another RED→GREEN cycle before full training.

### Task 7: Canonical local 100K training

**Artifacts:**
- Input: `/mnt/data/omega13_work/omega1_2_compiler_100k_FINAL.jsonl.gz`
- Output: `/mnt/data/omega13_work/checkpoints/omega13_graph_cortex_best.pt`
- Output metrics: `/mnt/data/omega13_work/results/omega13_dev_selection.json`

- [ ] **Step 1:** Verify corpus SHA and exact split counts before training.
- [ ] **Step 2:** Fit vocabulary from train only.
- [ ] **Step 3:** Train on all 100,000 train examples, max 8 epochs, CPU, batch 128 if memory permits otherwise 64.
- [ ] **Step 4:** Evaluate dev each epoch and freeze the best checkpoint using dev strict graph accuracy; do not read blind.
- [ ] **Step 5:** Save checkpoint SHA-256 and dev selection report.

### Task 8: One-shot blind evaluation and promotion gate

**Artifacts:**
- Output: `/mnt/data/omega13_work/results/omega13_blind_final.json`

- [ ] **Step 1:** Hash/freeze the selected checkpoint.
- [ ] **Step 2:** Run exactly one blind evaluation on 10,000 frozen rows.
- [ ] **Step 3:** Compare against Ω-1.2 baseline: relation 40%, strict graph 0%.
- [ ] **Step 4:** Calculate promotion gate: relation >40%, strict >0%, invalid accepted=0%, contamination=false.
- [ ] **Step 5:** Do not generate 250K if the gate fails.

### Task 9: Repository integration and evidence

**Files:**
- Update: `README.md`
- Add: `docs/results/2026-09-15-omega13-local-100k.md`
- Add/modify Ω-1.3 source/training/benchmark/tests from Tasks 1–5.

- [ ] **Step 1:** Push the exact locally verified source files to `nexus-gllm-omega1-v1`.
- [ ] **Step 2:** Document measured dev/blind metrics, parameter count, runtime, checkpoint/corpus hashes and promotion result without inflating synthetic-benchmark claims.
- [ ] **Step 3:** Update draft PR #1 description with Ω-1.3 evidence.
- [ ] **Step 4:** Inspect GitHub Actions status; keep PR draft unless remote CI is genuinely green.
