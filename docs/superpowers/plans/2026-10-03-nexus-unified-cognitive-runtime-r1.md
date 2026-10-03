# NEXUS Unified Cognitive Runtime R1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one canonical NEXUS runtime that composes the recovered NEXUS V7.2 neural cognitive cortex, CRC learned closed-loop policy, CRC-R1 cognitive organs, and R1.3-X Russian multi-turn dialogue/governor without conflating their responsibilities.

**Architecture:** Russian text enters through a compatibility ingress, V7.2 emits cognitive logits/features rather than prose, an adapter maps those features into MetaPolicy inputs, CRC-R2 chooses cognitive control parameters, CRC-R1 executes memory/causal/future-tree/reward/credit mechanisms, R1.3-X owns Russian dialogue state/governance/rendering, and observations close the RPE→credit→policy-update loop. V7.2 remains a non-autoregressive cognitive encoder; no generated language is attributed to it.

**Tech Stack:** Python 3, PyTorch, existing `nexus_gllm.unified_v3.cognitive` CRC modules, recovered R1.3-X runtime, pytest/GitHub Actions, real `nexus_ru_cortex_v7_2_i_curriculum.pt` for local end-to-end validation.

**Spec:** Current project checkpoint in this conversation: `REAL NEURAL CORTEX + REAL LEARNED LOOP + REAL RUSSIAN DIALOGUE RUNTIME` must become one runtime.

## Global Constraints

- Preserve component identity: V7.2 cortex != language generator; R1.3-X != neural cortex; CRC-R2 learned policy != all cognition.
- No external Qwen/Llama capability may be reported as native NEXUS cognition.
- No benchmark case may update policy during frozen evaluation.
- Fresh benchmark prompts/case IDs are authored and frozen before first result open.
- Keep FTX1 consumed; do not reuse it as untouched OOS.
- The real V7.2 checkpoint SHA-256 is `5a2c0c74cc25a9d4a17dc3575e299c8fbd2ed6b7a3115ebba439ba93484cfdfa`.
- R1.3-X V2 historical source anchor is commit `4735ca4f36d441f4fa2de6af4c704d5140a6c586`; integration must preserve equivalent dialogue/governor semantics rather than relabeling it as CRC.

## Review Focus

- Missing/malformed V7.2 checkpoint must fail closed without silently substituting another model.
- V7.2 output dimensions must be checked (`plan=14`, `rel=2`, `role=8`, `temp=3`) before use.
- A dialogue turn that CRC cannot support must preserve R1.3-X abstention rather than invent an answer.
- Frozen evaluation must verify parameter hashes are unchanged before/after evaluation.
- Policy improvement claims require fresh IID/OOD deltas, not only training reward.

---

### Task 1: Unified contracts and V7.2 cortex adapter

**Files:**
- Create: `src/nexus_gllm/unified_runtime/__init__.py`
- Create: `src/nexus_gllm/unified_runtime/types.py`
- Create: `src/nexus_gllm/unified_runtime/v72_cortex.py`
- Test: `tests/unified_runtime/test_v72_cortex.py`

**Interfaces:**
- Consumes: a PyTorch checkpoint path and Russian text/token IDs from a tokenizer callback.
- Produces: `CortexDecisionFeatures` with normalized plan/relation/role/temporal probability vectors, entropy/uncertainty summaries and provenance.

- [ ] Write tests first for exact head dimensions, deterministic inference in eval mode, checkpoint SHA enforcement, and fail-closed behavior.
- [ ] Run the tests and confirm RED because unified runtime modules do not exist.
- [ ] Implement the minimal V7.2 model reconstruction/adapter needed to load the recovered checkpoint without adding a language-generation head.
- [ ] Run focused tests to GREEN and commit.

### Task 2: Learned MetaPolicy bridge

**Files:**
- Create: `src/nexus_gllm/unified_runtime/learned_meta.py`
- Test: `tests/unified_runtime/test_learned_meta.py`

**Interfaces:**
- Consumes: `CortexDecisionFeatures`, CRC state uncertainty/novelty/self-model signals and compute budget.
- Produces: `LearnedMetaDecision` (`expert_top_k`, `branch_depth`, `branch_fanout`, `memory_limit`, `verification_level`, action distribution/value estimate) plus update telemetry.

- [ ] Write tests first proving RPE/credit changes policy parameters on TRAIN episodes and that frozen evaluation changes no parameter hashes.
- [ ] Run RED.
- [ ] Implement the policy/value bridge and recursive-credit update contract, preserving the previously demonstrated closed-loop semantics.
- [ ] Run GREEN and commit.

### Task 3: R1.3-X Russian dialogue compatibility layer

**Files:**
- Create: `src/nexus_gllm/unified_runtime/r13x_dialogue.py`
- Test: `tests/unified_runtime/test_r13x_dialogue.py`

**Interfaces:**
- Consumes: Russian text/session ID plus optional verified CRC result/evidence.
- Produces: Russian response, intent, abstention flag, evidence, memory/world-state change and provenance.

- [ ] Write tests for session memory, memory clear, world-state revision, anaphora/focus, causal chain, relation binding and abstention.
- [ ] Run RED.
- [ ] Port/bridge the exact R1.3-X V2 semantics required by these tests without changing the historical component's identity.
- [ ] Run GREEN and commit.

### Task 4: End-to-end NEXUS Cognitive Runtime

**Files:**
- Create: `src/nexus_gllm/unified_runtime/runtime.py`
- Test: `tests/unified_runtime/test_runtime.py`

**Interfaces:**
- Consumes: Russian turn + session ID + optional observed reward after action.
- Produces: `UnifiedRuntimeResponse` containing rendered Russian text and a complete trace across cortex→meta-policy→CRC→governor plus an episode handle for later observation.

- [ ] Write failing integration tests showing V7.2 features affect control decisions, R1.3-X preserves dialogue continuity, CRC trace exists and an observation updates the learned policy only when learning is enabled.
- [ ] Run RED.
- [ ] Wire the three layers in one runtime; keep generation and cognition provenance separate.
- [ ] Run GREEN and commit.

### Task 5: Real-checkpoint local validation and frozen Russian benchmark

**Files:**
- Create: `benchmarks/unified_runtime/fresh_ru_cases.json`
- Create: `benchmarks/unified_runtime/run_fresh_ru.py`
- Create: `docs/results/2026-10-03-unified-runtime-r1.md`
- Create: `.github/workflows/unified-runtime-r1.yml`

**Interfaces:**
- Consumes: frozen source commit, real V7.2 checkpoint by exact SHA, fresh Russian multi-turn cases.
- Produces: raw transcripts, per-turn pass/fail, dialogue-category metrics, learned-policy frozen hash verification and an evidence report.

- [ ] Author and commit fresh benchmark cases before first open.
- [ ] Run locally with the real Drive checkpoint and record raw transcripts rather than summaries only.
- [ ] Verify checkpoint SHA and policy pre/post hashes.
- [ ] Run the full unit/integration suite.
- [ ] Add CI that runs source-level tests without pretending the binary checkpoint is present when it is not.
- [ ] Commit report/evidence and open a PR; do not merge without an explicit later instruction.
