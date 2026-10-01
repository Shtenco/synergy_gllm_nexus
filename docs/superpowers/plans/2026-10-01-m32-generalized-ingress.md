# M32 Generalized Semantic + Task Ingress Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an authority-safe RU/EN/multisource ingress path that turns prompt/history/documents into grounded semantic atoms, a typed `TaskProgram`, and an admitted executable `ProgramNode` for the existing CRC reasoning stack.

**Architecture:** Add a new M32 ingress stack beside frozen R1. Neural/deterministic backends remain proposal-only; NEXUS recomputes source hashes, validates spans and ASTs, assigns authority, builds a transient reasoning world, and passes only admitted typed structures into `CognitiveLoopR1`. `ConversationalReasonerR1` remains byte-unchanged for FTX1 reproducibility; M32 adds `ConversationalReasonerR2`.

**Tech Stack:** Python 3, dataclasses, typing `Protocol`, existing NEXUS semantic/task/program contracts, pytest, existing Ollama transport abstraction.

**Spec:** `docs/superpowers/specs/2026-10-01-m32-generalized-ingress-design.md`

## Global Constraints

- Base lineage remains frozen CRC-R1 commit `fded8bd46777b2e868620b4c85d60c5c375b5ec1`; do not modify `ConversationalReasonerR1` semantics.
- FTX1 is `CONSUMED_FTX1` diagnostic only and cannot be used as clean OOS or as a training/threshold-selection source.
- Model backends have zero truth, commit, execution, action, or scoring authority.
- Every admitted semantic/task/program proposal must be grounded to immutable `SourceEnvelope` text by recomputed SHA-256 spans.
- Durable `ConversationShellR1.world` remains verified-only; asserted context is transient and never silently promoted.
- Malformed/backend-failure paths fail closed to rejection/`UNRESOLVED`; no retries that alter semantics.
- Existing CRC-R1 regression suite must remain green.
- Initial M32-DEV gates: task admission >=95%, admitted span/provenance validity 100%, program admission on solvable DEV >=90%, end-to-end strict on solvable DEV >=80%, unsafe authority promotions 0.

## Review Focus

- Unicode/cyrillic source-local offsets must hash exact Python character slices, not UTF-8 byte offsets; Task 1 pins RU mixed-text spans.
- Duplicate/unknown `source_id` values must fail closed rather than alias provenance; Task 1 pins duplicate and missing-source cases.
- A program that references operators absent from admitted context/task and not in structural built-ins must be rejected; Task 3 pins operator smuggling.
- Backend JSON/transport exceptions or malformed AST payloads must not leak partial proposals into execution; Task 4 pins fail-closed behavior.
- Asserted context must be usable transiently while leaving durable verified world unchanged; Task 2 and Task 5 pin both halves of this invariant.

---

### Task 1: Multi-source generalized ingress contracts and span gate

**Files:**
- Create: `src/nexus_gllm/unified_v3/cognitive/generalized_ingress.py`
- Test: `tests/m32/test_generalized_ingress.py`

**Interfaces:**
- Produces: `SourceKind`, `TrustClass`, `SourceEnvelope`, `GroundedSpanRef`, `GeneralizedSemanticAtomProposal`, `GeneralizedTaskProposal`, `GeneralizedIngressProposal`, `GeneralizedIngressRequest`, `GeneralizedIngressAdmission`, `GeneralizedIngressResult`, `GeneralizedIngressBackend`, `GeneralizedIngressR1.parse(request) -> GeneralizedIngressResult`.
- `GeneralizedIngressRequest.from_texts(prompt: str, history: tuple[str, ...] = (), documents: tuple[str, ...] = ()) -> GeneralizedIngressRequest` assigns deterministic source IDs and SHA-256 hashes.
- `GeneralizedIngressR1` validates source uniqueness, hashes, grounded spans, semantic identifiers, typed task shape and confidence, but does not assign truth authority.

- [ ] **Step 1: Write failing contract/gate tests**

Add tests asserting: deterministic source IDs/hashes; valid RU and EN spans admit; a Cyrillic substring hash uses Python character offsets; duplicate source IDs reject; unknown source IDs reject; out-of-range/hash-mismatched spans reject; backend exception returns a rejected result with no semantic/task/program outputs.

- [ ] **Step 2: Run the focused tests and confirm failure**

Run: `pytest tests/m32/test_generalized_ingress.py -v`

Expected: FAIL because `generalized_ingress` contracts do not exist.

- [ ] **Step 3: Implement minimal generalized ingress core**

Implement the interfaces above with immutable dataclasses, deterministic SHA-256 recomputation, identifier limits compatible with existing language/task gates, and fail-closed backend exception handling.

- [ ] **Step 4: Run focused tests**

Run: `pytest tests/m32/test_generalized_ingress.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -am "feat(m32): add grounded generalized ingress contracts"`

---

### Task 2: Authority-preserving transient reasoning context

**Files:**
- Create: `src/nexus_gllm/unified_v3/cognitive/reasoning_context.py`
- Test: `tests/m32/test_reasoning_context.py`

**Interfaces:**
- Consumes: admitted semantic atoms/spans from Task 1, `SemanticCommitGate`, `SemanticFactStatus`, `WorldHypothesis`.
- Produces: `ReasoningFact`, `ReasoningContextView`, `ReasoningContextBuilder.build(verified_world, ingress, attestations=()) -> ReasoningContextView`.
- `ReasoningContextView.execution_world` contains verified facts plus admitted `ASSERTED_CONTEXT`; `durable_world` remains the original verified world.

- [ ] **Step 1: Write failing authority tests**

Assert: a user/history/document assertion becomes transient `ASSERTED_CONTEXT`; it is present in `execution_world`; it is absent from `durable_world`; model-only proposals without user/evidence authority are not promoted; trusted contradiction rejects; verified evidence remains verified.

- [ ] **Step 2: Verify tests fail**

Run: `pytest tests/m32/test_reasoning_context.py -v`

Expected: FAIL because `ReasoningContextBuilder` does not exist.

- [ ] **Step 3: Implement `ReasoningContextBuilder`**

Reuse `SemanticCommitGate` decisions. Convert admitted semantic atoms to `WorldFact` only for transient execution when status is `ASSERTED_CONTEXT` or `VERIFIED`; preserve source/provenance IDs in `ReasoningFact` records; never mutate the supplied durable world.

- [ ] **Step 4: Run focused and legacy authority tests**

Run: `pytest tests/m32/test_reasoning_context.py tests/crc_r1/test_semantic_authority.py tests/crc_r1/test_conversation_shell.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -am "feat(m32): add transient authority-safe reasoning context"`

---

### Task 3: Program proposal contract and deterministic admission gate

**Files:**
- Create: `src/nexus_gllm/unified_v3/cognitive/program_proposal.py`
- Test: `tests/m32/test_program_proposal.py`

**Interfaces:**
- Consumes: `ProgramNode`, `ProgramKind`, Task 1 grounded spans, admitted task, `ReasoningContextView`.
- Produces: `ProgramProposal`, `ProgramAdmission`, `ProgramProposalGate.check(proposal, request, task, context) -> ProgramAdmission`.
- Default bounds: `min_confidence=0.80`, `max_depth=6`, `max_nodes=64`.
- Structural built-ins may be referenced only from an explicit constant allowlist; side-effect/action nodes do not exist in the admitted vocabulary.

- [ ] **Step 1: Write failing AST admission tests**

Assert: valid `ATOM`, `SEQUENCE`, `COMPOSE`, `IF`, `INHIBIT`, `TEMPORAL`, `COUNTERFACTUAL` trees admit when grounded; excessive depth/node count rejects; bad provenance rejects; unknown kind/payload rejects during decoding; operator smuggling rejects; confidence below 0.80 rejects.

- [ ] **Step 2: Verify tests fail**

Run: `pytest tests/m32/test_program_proposal.py -v`

Expected: FAIL because program proposal gate does not exist.

- [ ] **Step 3: Implement proposal gate**

Implement recursive AST validation without execution. Count nodes/depth from `ProgramNode`; derive the allowed operator set from the admitted task and context; require at least one valid supporting span.

- [ ] **Step 4: Run focused + existing program tests**

Run: `pytest tests/m32/test_program_proposal.py tests/crc_r1/test_program_compiler.py tests/crc_r1/test_program_synthesis.py tests/crc_r1/test_higher_order.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -am "feat(m32): gate grounded program AST proposals"`

---

### Task 4: One-call generalized Ollama proposal backend

**Files:**
- Create: `src/nexus_gllm/unified_v3/cognitive/generalized_ingress_ollama.py`
- Test: `tests/m32/test_generalized_ingress_ollama.py`

**Interfaces:**
- Consumes: Task 1 `GeneralizedIngressBackend` protocol and Task 3 program proposal schema; existing `OllamaModelRef` / `OllamaTransport`.
- Produces: `OllamaGeneralizedIngressBackend(model_ref: OllamaModelRef, transport=None)` with `propose(request) -> GeneralizedIngressProposal`.
- Model digest must be exactly 64 hex chars; request uses temperature 0 and strict JSON; payload exposes source IDs/text but no gold/scorer fields.

- [ ] **Step 1: Write failing mock-transport tests**

Assert: one backend call can return coherent semantic/task/program proposals across prompt/history/documents; source-local offsets are preserved; invalid model digest raises before transport; malformed JSON/unknown source/bad AST becomes fail-closed through `GeneralizedIngressR1`; transport exception leaks no partial proposal.

- [ ] **Step 2: Verify tests fail**

Run: `pytest tests/m32/test_generalized_ingress_ollama.py -v`

Expected: FAIL because backend does not exist.

- [ ] **Step 3: Implement minimal backend**

Follow the verified-model pattern in `ollama_ingress.py`, but emit the M32 combined proposal schema. Do not answer the user; prompt explicitly requests extraction/typed AST only.

- [ ] **Step 4: Run focused + legacy Ollama tests**

Run: `pytest tests/m32/test_generalized_ingress_ollama.py tests/crc_r1/test_ollama_ingress.py tests/crc_r1/test_ollama_surface.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -am "feat(m32): add generalized Ollama proposal backend"`

---

### Task 5: `ConversationalReasonerR2` end-to-end orchestration

**Files:**
- Create: `src/nexus_gllm/unified_v3/cognitive/conversational_reasoner_r2.py`
- Test: `tests/m32/test_conversational_reasoner_r2.py`

**Interfaces:**
- Consumes: `GeneralizedIngressR1`, `ReasoningContextBuilder`, `ProgramProposalGate`, existing `ProgramSynthesisCortex`, `CognitiveLoopR1`, `ConversationShellR1` surface renderer.
- Produces: `ConversationalRequest(prompt: str, history: tuple[str, ...] = (), documents: tuple[str, ...] = ())`, `ConversationalReasoningResultR2`, `ConversationalReasonerR2.answer(request, *, attestations=(), program_evidence=(), novelty=.5, uncertainty=.5, capability_hints=('program_execution',))`.
- Program selection order: admitted program proposal; otherwise existing synthesis with supplied grounded evidence; otherwise `UNRESOLVED`.

- [ ] **Step 1: Write failing integration tests with deterministic fixture backend**

Assert: RU and EN free-text requests can admit a task; history/document asserted atoms enter only transient execution world; an admitted program reaches `CognitiveLoopR1`; malformed proposal returns `UNRESOLVED`; no admitted program and no evidence returns `UNRESOLVED`; durable shell world is unchanged; R1 class/file behavior remains unchanged.

- [ ] **Step 2: Verify tests fail**

Run: `pytest tests/m32/test_conversational_reasoner_r2.py -v`

Expected: FAIL because R2 does not exist.

- [ ] **Step 3: Implement R2 orchestration**

Build the generalized request, parse once, construct the authority-safe execution view, select an admitted program or evidence-ranked synthesis, then call `CognitiveLoopR1.deliberate`. Reuse R1 epistemic projection/surface semantics without modifying R1.

- [ ] **Step 4: Run integration + frozen R1 reasoner tests**

Run: `pytest tests/m32/test_conversational_reasoner_r2.py tests/crc_r1/test_conversational_reasoner.py tests/crc_r1/test_cognitive_loop.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -am "feat(m32): add generalized conversational reasoner r2"`

---

### Task 6: Fresh M32-DEV benchmark and acceptance gates

**Files:**
- Create: `benchmarks/m32_dev/generator.py`
- Create: `benchmarks/m32_dev/evaluate.py`
- Create: `benchmarks/m32_dev/README.md`
- Create: `tests/m32/test_m32_dev.py`

**Interfaces:**
- Produces deterministic fresh DEV cases spanning RU, EN, mixed language, history, documents, composition, counterfactual, conflict and adversarial malformed proposals.
- `evaluate.run(seed: int = 32001) -> dict` returns at least `cases`, `task_admission`, `provenance_validity`, `program_admission_solvable`, `e2e_strict_solvable`, `unsafe_authority_promotions`, and per-family metrics.
- DEV uses deterministic fixture/model-stub proposal backend for architecture correctness; it does not claim neural quality.

- [ ] **Step 1: Write failing benchmark-gate test**

Generate a fixed corpus and assert the report contains all required metrics, no family is empty, provenance/authority gates are exact, and the fixture architecture meets the spec targets.

- [ ] **Step 2: Verify failure**

Run: `pytest tests/m32/test_m32_dev.py -v`

Expected: FAIL because benchmark does not exist.

- [ ] **Step 3: Implement generator/evaluator**

Do not copy or derive cases from FTX1. Label the benchmark `M32-DEV`, not OOS. Include explicit negative/fail-closed cases separately from solvable strict cases.

- [ ] **Step 4: Run DEV benchmark and full M32 tests**

Run: `python -m benchmarks.m32_dev.evaluate && pytest tests/m32 -v`

Expected: all engineering gates pass; fixture DEV meets the target thresholds.

- [ ] **Step 5: Commit**

`git commit -am "test(m32): add fresh generalized ingress dev benchmark"`

---

### Task 7: M32-META freeze harness, regression suite, and evidence report

**Files:**
- Create: `benchmarks/m32_meta/generator.py`
- Create: `benchmarks/m32_meta/freeze.py`
- Create: `benchmarks/m32_meta/README.md`
- Create: `tests/m32/test_m32_meta_freeze.py`
- Create: `docs/results/2026-10-01-m32-generalized-ingress.md`

**Interfaces:**
- `m32_meta.generator` uses an independent seed/family configuration from DEV.
- `freeze.build_manifest(...) -> dict` records generator SHA-256, seed, case count, M32 implementation commit, and `ftx1_used_as_clean_oos=false`.
- The META corpus is generated/sealed before its first integrated evaluation and is not edited after scoring.

- [ ] **Step 1: Write failing freeze-policy tests**

Assert deterministic generator hash/seed, manifest commit binding, DEV/META seed separation, explicit FTX1 consumed marker, and refusal to overwrite an existing sealed manifest with changed generator/hash.

- [ ] **Step 2: Verify tests fail**

Run: `pytest tests/m32/test_m32_meta_freeze.py -v`

Expected: FAIL because META freeze tooling does not exist.

- [ ] **Step 3: Implement META freeze harness and result template**

Do not author FTX2 here. This task only establishes an independent development meta gate and records the scientific boundary that FTX2 comes after M32 thresholds/architecture freeze.

- [ ] **Step 4: Run complete regression verification**

Run: `pytest tests/m32 tests/crc_r1 tests/hard_oos_f tests/hard_oos_f2 tests/crc_meta_g -v`

Expected: PASS with zero frozen-path regressions.

Run: `git diff fded8bd46777b2e868620b4c85d60c5c375b5ec1 -- src/nexus_gllm/unified_v3/cognitive/conversational_reasoner.py`

Expected: no diff.

- [ ] **Step 5: Record evidence and commit**

Write actual commands/results/hashes into `docs/results/2026-10-01-m32-generalized-ingress.md`, clearly separating fixture architecture scores from future real-neural quality and from future FTX2 generalization.

`git commit -am "docs(m32): freeze meta protocol and record ingress evidence"`

---

## Final verification gate

Before calling M32 complete:

- `pytest tests/m32 -v` must pass.
- Frozen CRC-R1 regression suites named in Task 7 must pass.
- `ConversationalReasonerR1` must have no source diff from `fded8bd...`.
- No FTX1 case/gold/prediction content may be present in M32 benchmark generation or threshold selection.
- Any real neural backend evaluation must pin a concrete model artifact/digest and be reported separately from fixture results.
- M32 may be declared engineering-complete after DEV/META gates; broad generalization remains unproven until a newly authored, newly sealed FTX2 is opened once after an M32 freeze.
