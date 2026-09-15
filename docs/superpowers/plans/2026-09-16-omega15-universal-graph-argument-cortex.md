# NEXUS GLLM Ω-1.5 Universal Graph Argument Cortex Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a joint Russian text→graph triple constructor that couples Ω-1.4 canonical relation semantics with relation-conditioned SUBJECT/OBJECT/EVENT/CONTEXT argument extraction, trains locally on 100K, and is evaluated once on frozen Blind-3.

**Architecture:** A multi-scale candidate-node proposal layer produces typed spans (1–6 words plus event/clause/context chunks). Ω-1.4 relation scores initialize canonical operator states. A recurrent factor-graph matcher jointly scores `(subject, object, relation)` and iteratively refines operator and role states to a fixed point. Strong Ω-1.4 semantic evidence remains sovereign; neural refinement may improve ambiguous cases but may not overwrite verified operator evidence.

**Tech Stack:** Python 3.11+, PyTorch 2.x CPU, gzip/json, pytest.

**Spec:** `docs/superpowers/specs/2026-09-16-omega15-universal-graph-argument-cortex-design.md`

## Global Constraints

- No pretrained LLM, tokenizer, embedding model, or external runtime backbone.
- Blind-3A/B were frozen before Ω-1.5 model code and are forbidden during architecture, threshold, loss-weight, or checkpoint selection.
- Shadow-Dev-3 is the only Ω-1.5 perturbation tuning surface.
- Candidate nodes support 1–6-word spans plus event/clause/context chunks.
- Top-K candidate nodes defaults to 48 and must be configurable.
- Joint inference refines SUBJECT/OBJECT/RELATION for at most 4 recurrent rounds and may stop early after two stable rounds.
- Ω-1.4 semantic evidence remains sovereign when its evidence margin exceeds the frozen threshold.
- Stage-A protected relation accuracy may not regress from the Ω-1.4 frozen baseline.
- Argument candidate recall@48 must reach at least 99% on Stage-A dev + Shadow-Dev-3 before Blind-3 is opened.
- Canonical local run uses seed 17 and resumable optimizer state across CPU process chunks.
- Promotion to 250K requires Blind-3 joint triple improvement, NOTA precision >=98%, invalid accepted mutation rate 0%, and protected-regression gates passing.

---

### Task 1: Multi-scale typed candidate-node lattice

**Files:**
- Create: `src/nexus_gllm/argument_candidates.py`
- Create: `tests/test_argument_candidates.py`

**Interfaces:**
- `ArgumentCandidate(span: tuple[int,int], text: str, word_count: int, candidate_type: str, clause_id: int, features: tuple[float,...])`
- `build_argument_candidates(text: str, *, max_words: int = 6, top_k: int = 48) -> list[ArgumentCandidate]`
- candidate types: `ENTITY`, `EVENT`, `CONTEXT`, `GENERIC`, `NULL`.

- [ ] **Step 1: Write failing tests** covering 1–6-word spans, punctuation-safe char offsets, event-clause candidates, no duplicate spans, deterministic ordering, and `top_k` truncation.
- [ ] **Step 2: Run** `PYTHONPATH=src pytest -q tests/test_argument_candidates.py` and require RED because the module does not exist.
- [ ] **Step 3: Implement deterministic token/clause segmentation** without external NLP dependencies; generate contiguous word spans length 1–6 plus clause-level candidates, score cheap boundary/type features, deduplicate by char span, and keep top-K.
- [ ] **Step 4: Re-run targeted tests** and require PASS.
- [ ] **Step 5: Add corpus coverage test** asserting Stage-A dev + Shadow-Dev-3 gold subject/object spans are representable at `K=48`; record recall@48.

### Task 2: Relation-conditioned role scorer

**Files:**
- Create: `src/nexus_gllm/argument_roles.py`
- Create: `tests/test_argument_roles.py`

**Interfaces:**
- `RoleScorer(nn.Module)` consumes candidate embeddings, operator embedding, global sentence embedding, and role id.
- Returns `subject_logits`, `object_logits`, `event_logits`, `context_logits` over candidates plus NULL.

- [ ] **Step 1: Write failing tests** for tensor shapes, padding masks, relation conditioning, finite gradients, and role-specific parameter separation.
- [ ] **Step 2: Verify RED** with `pytest -q tests/test_argument_roles.py`.
- [ ] **Step 3: Implement biaffine/dot-product role scores** using candidate projection + operator-conditioned query vectors; NULL is a learned candidate.
- [ ] **Step 4: Add graph-compatibility bias** from `OperatorCard` family/type compatibility without allowing the bias to choose a relation by itself.
- [ ] **Step 5: Run tests** and require PASS.

### Task 3: Joint triple factor graph and fixed-point refinement

**Files:**
- Create: `src/nexus_gllm/triple_factor_graph.py`
- Create: `tests/test_triple_factor_graph.py`

**Interfaces:**
- `TripleState(relation_logits, subject_logits, object_logits, triple_scores, iteration, converged)`.
- `JointTripleFactorGraph(nn.Module).forward(...) -> TripleState`.
- Factor score:
  `F(s,o,r)=S_relation(r)+A_subject(s|r)+A_object(o|r,s)+G(s,o,r)`.

- [ ] **Step 1: Write failing tests** showing a relation update can change role ranking and a role update can change relation ranking; test fixed-point early stop after two stable iterations.
- [ ] **Step 2: Run tests** and verify RED.
- [ ] **Step 3: Implement joint score tensor** efficiently for `K<=48`, six known relations, plus NOTA/NULL handling.
- [ ] **Step 4: Implement 4-round recurrent refinement** with small GRUCell states for relation, subject and object; each round reads soft expected counterpart embeddings.
- [ ] **Step 5: Implement convergence rule**: same top `(s,o,r)` and margin change < configurable epsilon for two consecutive rounds.
- [ ] **Step 6: Run tests** and require PASS.

### Task 4: UniversalGraphArgumentCortex integration

**Files:**
- Create: `src/nexus_gllm/argument_cortex.py`
- Create: `tests/test_argument_cortex.py`
- Reuse: `src/nexus_gllm/semantic_relation.py`, `src/nexus_gllm/operator_space.py`

**Interfaces:**
- `UniversalGraphArgumentCortex.forward(batch) -> dict[str, Tensor]`.
- `predict(text, omega14_semantics, ...) -> GraphTripleProposal`.
- `GraphTripleProposal(subject_span, object_span, relation, confidence, converged, evidence)`.

- [ ] **Step 1: Write failing end-to-end tests** for `owned_by`, `located_in`, temporal event pair, long multi-word arguments, NOTA and argument reversal.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: Implement candidate embedding** from hashed char n-grams + deterministic morphology/type features + local char pooling; keep model CPU-realistic (<3M Ω-1.5-added parameters).
- [ ] **Step 4: Integrate frozen/loaded Ω-1.4 relation evidence** as the initial operator score.
- [ ] **Step 5: Add sovereign semantic gate** so high-margin Ω-1.4 evidence cannot be overwritten by joint refinement; ambiguous evidence remains refinable.
- [ ] **Step 6: Run tests** and require PASS.

### Task 5: Ω-1.5 dataset, train bank and Blind-3 guard

**Files:**
- Create: `training/omega15_dataset.py`
- Create: `tests/test_omega15_dataset.py`

**Interfaces:**
- Dataset returns text, relation target, subject/object spans, candidate indices, type targets, transformation family, and protected flag.
- `assert_training_path_allowed(path)` rejects `blind3a`, `blind3b`, and frozen Blind-3 directories.

- [ ] **Step 1: Write failing tests** for exact candidate-index alignment, NULL targets, long arguments, multi-clause rows and Blind-3 guard.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: Implement Stage-A→Ω-1.5 train augmentation** using train/shadow-safe transformations only: namespace variation, clause distractors, multi-word argument aliases, role-preserving reorderings, and event wrappers. Do not import Blind-3 templates.
- [ ] **Step 4: Build deterministic 100K train view** and 12K Shadow-Dev-3 loader.
- [ ] **Step 5: Run tests** and require PASS.

### Task 6: Joint structured losses

**Files:**
- Create: `training/omega15_losses.py`
- Create: `tests/test_omega15_losses.py`

**Interfaces:**
- `omega15_loss(outputs, batch, weights) -> dict[str, Tensor]` with scalar `total`.

Loss terms:
- `L_node`: candidate boundary/type supervision.
- `L_subject`, `L_object`: role CE including NULL.
- `L_relation`: protected Ω-1.4 relation CE/distillation.
- `L_triple`: structured CE over gold `(s,o,r)`.
- `L_consistency`: OperatorCard role/type violations.
- `L_null`: NOTA/unknown rows should choose NULL roles.
- `L_replay`: protected Ω-1.4 score retention.
- `L_entity_bias`: counterfactual entity-name swap should preserve relation prediction.

- [ ] **Step 1: Write failing scalar/gradient tests** for every component and verify `total.backward()` reaches candidate and joint-factor parameters.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: Implement losses** with configurable weights and no loss contribution from missing gold roles where masks say unavailable.
- [ ] **Step 4: Run tests** and require PASS.

### Task 7: Trainer, protected gates and resumable CPU state

**Files:**
- Create: `training/train_omega15.py`
- Create: `training/resume_omega15.py`
- Create: `tests/test_omega15_training.py`

**Interfaces:**
- State stores model, optimizer, cursor, fixed permutation, RNG, best metrics, Ω-1.4 checkpoint hash, candidate-generator config and loss weights.

- [ ] **Step 1: Write failing tests** for one optimization step, deterministic resume, identical optimizer moments after save/load, and checkpoint metadata excluding Blind-3 metrics.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: Implement trainer** with AdamW, grad clip 1.0, batch auto-fallback, seed 17 and periodic dev/shadow evaluation.
- [ ] **Step 4: Implement selection tuple**: primary joint non-NOTA triple exact on Shadow-Dev-3; guards candidate recall@48>=99%, protected Stage-A relation no-regression, NOTA precision, invalid mutation rate.
- [ ] **Step 5: Implement resumable chunks** preserving the same permutation and AdamW state across fresh processes.
- [ ] **Step 6: Run tests** and require PASS.

### Task 8: Frozen Ω-1.5 benchmark

**Files:**
- Create: `benchmarks/run_omega15_benchmark.py`
- Create: `tests/test_omega15_benchmark.py`

**Metrics:**
- candidate recall@48 for subject/object/both;
- subject exact;
- object exact;
- both argument exact;
- relation accuracy with gold args;
- relation accuracy with predicted args;
- joint non-NOTA triple exact;
- NOTA precision/recall/F1;
- invalid accepted mutation rate;
- fixed-point convergence rate and mean iterations.

- [ ] **Step 1: Write failing metric-contract test** and promotion-gate test.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: Implement benchmark** with read-only model evaluation and explicit refusal to run Blind-3 from training code paths.
- [ ] **Step 4: Run tests** and require PASS.

### Task 9: Local verification before 100K

- [ ] **Step 1:** Run `PYTHONPATH=src:. pytest -q tests/test_argument_candidates.py tests/test_argument_roles.py tests/test_triple_factor_graph.py tests/test_argument_cortex.py tests/test_omega15_dataset.py tests/test_omega15_losses.py tests/test_omega15_training.py tests/test_omega15_benchmark.py`.
- [ ] **Step 2:** Run `python -m compileall src training benchmarks`.
- [ ] **Step 3:** Measure candidate recall@48 on Stage-A dev + Shadow-Dev-3; require >=99% before training.
- [ ] **Step 4:** Run a 20K diagnostic with no Blind-3 access. Require non-zero joint triple exact and no protected Ω-1.4 semantic regression before full 100K.

### Task 10: Canonical local 100K training

**Artifacts:**
- `/mnt/data/omega15_work/checkpoints/omega15_best.pt`
- `/mnt/data/omega15_work/checkpoints/omega15_full100k.pt`
- `/mnt/data/omega15_work/results/omega15_selection.json`

- [ ] **Step 1:** Verify Stage-A/train corpus and Ω-1.4 checkpoint SHA before training.
- [ ] **Step 2:** Train exactly 100,000 examples with seed 17 using resumable CPU chunks while preserving one optimizer state.
- [ ] **Step 3:** Evaluate Stage-A dev + Shadow-Dev-3 at every selection checkpoint; do not read Blind-3.
- [ ] **Step 4:** Freeze best eligible checkpoint according to Task 7 selection tuple and write SHA-256.
- [ ] **Step 5:** If no checkpoint passes pre-Blind protected gates, stop and do not open Blind-3.

### Task 11: One-shot Blind-3 and promotion decision

- [ ] **Step 1:** Freeze checkpoint hash and source/config hashes.
- [ ] **Step 2:** Run Blind-3A exactly once.
- [ ] **Step 3:** Run Blind-3B exactly once.
- [ ] **Step 4:** Compare Ω-1.5 against frozen Ω-1.4 on the same Blind-3 corpora.
- [ ] **Step 5:** Promotion to 250K requires: joint non-NOTA triple exact improves; candidate recall@48>=99%; relation regression <=1 pp; NOTA precision>=98%; invalid accepted mutation=0%; protected regressions=0.
- [ ] **Step 6:** Do not tune Ω-1.5 from Blind-3 results.

### Task 12: Repository integration and evidence

**Files:**
- Add Ω-1.5 source/training/benchmark/tests.
- Add: `docs/results/2026-09-16-omega15-local-100k.md`.
- Update draft PR #1.

- [ ] **Step 1:** Push only locally verified source files to `nexus-gllm-omega1-v1`.
- [ ] **Step 2:** Document actual 100K/dev/shadow/Blind-3 metrics and SHA-256 values without inflating synthetic-benchmark claims.
- [ ] **Step 3:** Update PR title/body to Ω-1.5 and keep it draft unless repository-wide CI is genuinely green.
- [ ] **Step 4:** Build a reproducibility ZIP containing source snapshot, checkpoint, frozen manifests, metrics and hashes.
