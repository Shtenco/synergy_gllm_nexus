# NEXUS Unified v2 + UB2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze NEXUS-UB2/1 before any v2 runtime implementation, then build and verify a 12-organ sovereign Unified NEXUS v2 with full UB1 coverage and one-shot UB2 promotion testing.

**Architecture:** A typed sovereign organ bus carries immutable semantic envelopes between independently ablatable organs. Only Formal Authority or Evidence Governor may commit factual claims; Surface Decoder has no factual authority and is checked against AnswerGraph by a semantic guard.

**Tech Stack:** Python 3.11+, dataclasses, pathlib/json/hashlib, numpy/joblib/torch only where existing donor organs already require them, pytest, existing `nexus_gllm` package.

**Spec:** `docs/superpowers/specs/2026-09-16-nexus-unified-v2-ub2-design.md`

## Global Constraints

- UB2 blind suite contains exactly 2,140 cases across 7 tracks: 300/300/300/300/300/320/320.
- UB2 must be fully generated, validated, hash-frozen and committed before the first `src/nexus_gllm/unified_v2/` implementation commit.
- No split-identifying lexical/entity prefixes.
- Graph D1-D8 declared depth must equal actual edge count.
- Research track uses only a frozen local evidence corpus for the headline benchmark.
- No post-Blind tuning.
- UB1 promotion gate: Full Strict >=80%; Formal >=90%; Semantic >=70%; Operator >=95%; Binding strict >=70%; Graph/Context/Evidence >=98%.
- UB2 promotion gate: Full >=70%; every track >=60%; deterministic Long Memory/Coreference/Research >=80%; fabricated citation <=1%; guard factual mutation rate 0.
- R7.44.3 remains `ADAPTER/REBUILT`, never `EXACT`, until R7.38 artifact identity is resolved.

---

### Task 1: UB2 schemas, generators and deterministic corpus

**Files:**
- Create: `benchmarks/ub2/schema.py`
- Create: `benchmarks/ub2/generator/generate_ub2.py`
- Create: `benchmarks/ub2/generator/evidence_corpus.py`
- Test: `tests/ub2/test_generator.py`

**Interfaces:**
- Produces `UB2Case`, `SemanticContract`, `EvidenceDocument` dataclasses.
- Produces deterministic `generate_all(seed: int) -> dict[str, list[UB2Case]]` with blind counts 300/300/300/300/300/320/320.

- [ ] Write failing tests asserting exact per-track counts, deterministic case IDs, no duplicate IDs, no split marker in text/metadata, declared graph depth equals actual path length, and evidence citations resolve to local corpus document IDs.
- [ ] Run `pytest tests/ub2/test_generator.py -v` and confirm failure before generator exists.
- [ ] Implement schema and generators with fixed seeds and capability-specific semantic contracts.
- [ ] Re-run generator tests and require all pass.
- [ ] Commit only UB2 generator/schema/tests; do not create v2 runtime code.

### Task 2: UB2 validators and scoring contract

**Files:**
- Create: `benchmarks/ub2/validators/validate_ub2.py`
- Create: `benchmarks/ub2/scoring/score_ub2.py`
- Test: `tests/ub2/test_validator.py`
- Test: `tests/ub2/test_scoring.py`

**Interfaces:**
- `validate_suite(cases) -> ValidationReport`
- `score_case(case, prediction) -> CaseScore`
- `score_suite(cases, predictions) -> SuiteScore`

- [ ] Write failing validator tests for count mismatch, duplicate ID, leaked split marker, wrong graph depth, invalid evidence reference and unresolved deterministic coreference gold.
- [ ] Write failing scoring tests for required/forbidden claims, clarification-required cases, stale-fact correction, citation alignment, abstention and guard mutation flags.
- [ ] Implement validators and scorer minimally.
- [ ] Run `pytest tests/ub2 -v`; require all tests pass.
- [ ] Commit validators/scorer/tests.

### Task 3: Generate and freeze UB2 before v2 code

**Files:**
- Create: `benchmarks/ub2/frozen/*.jsonl`
- Create: `benchmarks/ub2/frozen/NEXUS_UB2_FREEZE_MANIFEST.json`
- Create: `benchmarks/ub2/README.md`

**Interfaces:**
- Freeze manifest records generator commit, per-file SHA-256, case counts, seed, schema version and top-level suite digest.

- [ ] Run generator with the preregistered seed and produce the seven blind JSONL files plus local evidence corpus.
- [ ] Run `python benchmarks/ub2/validators/validate_ub2.py benchmarks/ub2/frozen` and require zero validation errors.
- [ ] Compute SHA-256 for every frozen artifact and write manifest.
- [ ] Recompute hashes independently and compare with manifest.
- [ ] Commit complete frozen UB2 suite and record freeze commit SHA in the manifest/provenance note.
- [ ] Verify repository history contains no `src/nexus_gllm/unified_v2/` implementation before this freeze commit.

### Task 4: Typed contracts, bus, workspace and provenance

**Files:**
- Create: `src/nexus_gllm/unified_v2/contracts.py`
- Create: `src/nexus_gllm/unified_v2/bus.py`
- Create: `src/nexus_gllm/unified_v2/workspace.py`
- Create: `src/nexus_gllm/unified_v2/provenance.py`
- Test: `tests/unified_v2/test_bus_workspace.py`

**Interfaces:**
- Immutable `TextTurn`, `EntityRef`, `Claim`, `ClaimProposal`, `EvidenceItem`, `AnswerGraph`, `ExecutionTrace`.
- `OrganBus.dispatch(envelope) -> tuple[Proposal,...]`
- `GraphWorkspace.commit(validated_claims)` and separate candidate store.

- [ ] Write failing tests proving proposal-only organs cannot commit facts and every bypass/organ call is traced.
- [ ] Implement immutable contracts and bus/workspace authority checks.
- [ ] Add provenance digests for organ/adapters/config.
- [ ] Run focused tests; commit.

### Task 5: Donor adapters for formal, Russian binder, morpholex and unseen reasoning

**Files:**
- Create: `src/nexus_gllm/unified_v2/organs/formal_authority.py`
- Create: `src/nexus_gllm/unified_v2/organs/russian_binder.py`
- Create: `src/nexus_gllm/unified_v2/organs/morpholex.py`
- Create: `src/nexus_gllm/unified_v2/organs/unseen_operator.py`
- Test: `tests/unified_v2/test_donor_adapters.py`

**Interfaces:**
- Each adapter exposes `organ_id`, `artifact_identity`, `supported_capabilities`, `propose(...)`.
- Formal authority alone may return `CommittedFormalDerivation` inside supported formal domain.

- [ ] Write contract tests using representative UB1 cases.
- [ ] Implement thin adapters without changing donor model weights/logic.
- [ ] Mark missing exact donor artifact as unavailable rather than silently substitute.
- [ ] Run adapter tests and donor regression tests; commit.

### Task 6: Semantic operator and universal role binder integration

**Files:**
- Create: `src/nexus_gllm/unified_v2/organs/semantic_operator.py`
- Create: `src/nexus_gllm/unified_v2/organs/role_binder.py`
- Test: `tests/unified_v2/test_semantic_role_pipeline.py`

**Interfaces:**
- Relation proposal -> relation-conditioned role proposal -> structured claim proposal.

- [ ] Write failing tests for active/passive order, swapped arguments, negation and multi-entity distractors.
- [ ] Adapt Ω-1.4R and Ω-1.5R2 frozen artifacts.
- [ ] Ensure identity/split markers are never introduced.
- [ ] Run tests and UB1 relation-binding adapter regression; commit.

### Task 7: Context Cortex v2

**Files:**
- Create: `src/nexus_gllm/unified_v2/organs/context_cortex.py`
- Test: `tests/unified_v2/test_context_cortex.py`

**Interfaces:**
- Maintains topic-scoped memory, `PendingSlotFrame`, anaphora resolution proposals, stale-fact invalidation and suspend/resume goals.

- [ ] Write failing tests for 30/50/75/100-turn memory, correction invalidation, topic switching, suspended goals and ambiguous coreference requiring clarification.
- [ ] Implement documented R7.44.3 contracts without claiming exact restoration.
- [ ] Run context tests and UB1 context track; commit.

### Task 8: Recurrent reasoning and Evidence Governor

**Files:**
- Create: `src/nexus_gllm/unified_v2/organs/recurrent_reasoner.py`
- Create: `src/nexus_gllm/unified_v2/organs/evidence_governor.py`
- Test: `tests/unified_v2/test_reasoning_governor.py`

**Interfaces:**
- Reasoner emits hypotheses only.
- Governor returns validated claims, contradictions, uncertainty and abstentions with evidence/proof traces.

- [ ] Write tests proving unsupported hypotheses never become committed facts.
- [ ] Adapt R7.17 loop and R7.18/R7.10 evidence/proof mechanisms through stable interfaces.
- [ ] Run UB1 formal/semantic/evidence regressions; commit.

### Task 9: Research Cortex adapter

**Files:**
- Create: `src/nexus_gllm/unified_v2/organs/research_cortex.py`
- Test: `tests/unified_v2/test_research_cortex.py`

**Interfaces:**
- Accepts QueryGraph; returns evidence proposals/citation ledger only.
- UB2 headline mode uses frozen local corpus; live federation is a separate runtime mode.

- [ ] Write tests for source conflict, copied/dependent source penalty, insufficient evidence and citation alignment.
- [ ] Adapt Ω-1.6 evidence graph/trust/scheduler contracts.
- [ ] Confirm no mutation authority; commit.

### Task 10: Surface Decoder and semantic guard

**Files:**
- Create: `src/nexus_gllm/unified_v2/organs/surface_decoder.py`
- Create: `src/nexus_gllm/unified_v2/guard.py`
- Test: `tests/unified_v2/test_surface_guard.py`

**Interfaces:**
- `render(answer_graph) -> str`
- `guard(answer_graph, text) -> GuardResult`

- [ ] Write failing tests for added numbers/entities, flipped negation, reversed causality, fabricated citation and excessive certainty.
- [ ] Implement deterministic faithful renderer baseline first.
- [ ] Add natural Russian realization layer only behind the same guard.
- [ ] Require factual mutation rate 0 on deterministic test suite; commit.

### Task 11: Unified v2 orchestration runtime

**Files:**
- Create: `src/nexus_gllm/unified_v2/runtime.py`
- Create: `src/nexus_gllm/unified_v2/config.py`
- Test: `tests/unified_v2/test_runtime.py`

**Interfaces:**
- `UnifiedNexusV2.respond(turn: TextTurn) -> UnifiedResponse`
- Supports per-organ ablation flags and complete execution traces.

- [ ] Write failing end-to-end tests for formal, operator, relation-binding, context, evidence and research flows.
- [ ] Implement capability routing and fail-closed error policy.
- [ ] Run full `tests/unified_v2`; commit.

### Task 12: Full UB1 adapters and score

**Files:**
- Create: `benchmarks/run_unified_v2_ub1.py`
- Create: `docs/results/UNIFIED_V2_UB1.json`

- [ ] Run all seven frozen UB1 tracks with no missing adapter.
- [ ] Calculate fixed-denominator Full Strict /970 and per-track gates.
- [ ] Run Unified v1 baseline through the same runner where interfaces permit and preserve historical current score separately.
- [ ] If UB1 Full <80% or any track gate fails, record failure; do not open UB2 blind.
- [ ] Commit raw UB1 results and hashes.

### Task 13: Dev/shadow, ablations and pre-Blind freeze

**Files:**
- Create: `benchmarks/ub2/run_dev_shadow.py`
- Create: `docs/results/UNIFIED_V2_ABLATIONS.json`
- Create: `benchmarks/ub2/frozen/UNIFIED_V2_PREBLIND_FREEZE.json`

- [ ] Run dev/shadow and one-organ-at-a-time ablations.
- [ ] Freeze every organ/adapter/config digest.
- [ ] Verify all unit/integration tests and compileall.
- [ ] Commit pre-Blind freeze.

### Task 14: One-shot UB2 blind and promotion decision

**Files:**
- Create: `docs/results/UNIFIED_V2_UB2_BLIND_ONE_SHOT.json`
- Create: `docs/results/UNIFIED_V2_FINAL_REPORT.md`

- [ ] Run the frozen blind suite exactly once against the frozen pre-Blind runtime.
- [ ] Calculate Full /2140 and all track/gate metrics.
- [ ] Record fabricated citation and semantic guard mutation rates.
- [ ] Decide `PROMOTED` only if every preregistered UB1/UB2 gate passes; otherwise record `FROZEN_FAILED_PROMOTION` with no post-Blind tuning.
- [ ] Run final SHA/integrity verification and commit results.
