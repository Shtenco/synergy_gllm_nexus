# NEXUS v3-MoE Generalization Federation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and train a hierarchical cost-aware Top-K Mixture-of-Experts that federates the strongest verified NEXUS capabilities while keeping Unified v3 as the sole sovereign world/hypothesis/verifier core.

**Architecture:** Historical NEXUS versions are wrapped as typed proposal experts. A learned capability router selects a small Top-K set, a novelty gate widens routing or invokes fast induction on novel tasks, lineage-aware proposal fusion converts expert outputs into v3 world/rule/task hypotheses, and the existing v3 executor/epistemic/generalization stack commits the final result. Historical experts never write final answers or mutate sovereign world state directly.

**Tech Stack:** Python >=3.11, dataclasses/enums/typing/hashlib/json/random, pytest >=8, PyTorch >=2.2, existing `src/nexus_gllm/unified_v3` and selected `unified_v2/organs` donor adapters.

**Spec:** `docs/superpowers/specs/2026-09-18-nexus-v3-moe-generalization-federation-design.md`

## Global Constraints

- FTX1 BLIND remains sealed and is never used for training, routing thresholds, calibration, ablations, or model selection.
- Historical experts emit `ExpertProposal` only; no expert has final answer or direct world-commit authority.
- No majority vote.
- Router inputs exclude benchmark name, track ID, split ID, case ID patterns, gold labels, renderer/template IDs, proof paths, or answer indices.
- Exact historical artifacts and reconstructed donor adapters must have distinct provenance labels.
- Expert artifact/checkpoint hash mismatch disables the expert fail-closed.
- Lineage-related experts do not count as independent evidence.
- Existing Unified v3 P0/P0.1 tests remain unchanged regression gates.
- HARD-OOS D is consumed and may inform curriculum design only; it cannot be reused as clean OOS evidence.
- Initial active expert set: R7-L, R7.2, R7.18, R7.44 context donor, Ω-1.5R2/graph donor, v3 hypothesis expert.
- R7.6, R7.8, R7.10, R7.14, V10, Unified R1.3, V30 start shadow/registry-only until adapter validation.
- Default learned routing uses Top-K 2..4 with cost-aware widening under novelty/disagreement.
- Final promotion requires measurable gain over the best single expert and low negative transfer.

---

### Task 1: MoE contracts and registry

**Files:**
- Create: `src/nexus_gllm/unified_v3/moe/__init__.py`
- Create: `src/nexus_gllm/unified_v3/moe/contracts.py`
- Create: `src/nexus_gllm/unified_v3/moe/registry.py`
- Create: `src/nexus_gllm/unified_v3/moe/lineage.py`
- Test: `tests/unified_v3_moe/test_contracts_registry.py`

**Interfaces:**
- Produces `ExpertMode`, `ExpertProvenanceKind`, `ExpertFailureFlag`, `CapabilityTag`.
- Produces frozen `ExpertProposal`, `ExpertSpec`, `RoutingDecision`, `FusedProposalSet`.
- Produces `ExpertRegistry.register(spec)`, `get(id)`, `active()`, `shadow()`, `verify_artifact(id)`.
- Produces `lineage_independence_weight(specs) -> dict[str,float]`.

- [ ] Write failing tests that construct a proposal and assert no `final_answer`/world-mutation field exists.
- [ ] Write failing hash-mismatch test asserting expert is disabled instead of loaded.
- [ ] Write lineage test asserting related experts receive discounted independent-support weights.
- [ ] Run `pytest tests/unified_v3_moe/test_contracts_registry.py -q` and observe RED.
- [ ] Implement contracts/registry/lineage minimally.
- [ ] Run focused test and existing `tests/unified_v3`; require GREEN.
- [ ] Commit `feat(v3-moe): add typed expert registry contracts`.

### Task 2: Base expert adapter and fail-closed execution

**Files:**
- Create: `src/nexus_gllm/unified_v3/moe/experts/__init__.py`
- Create: `src/nexus_gllm/unified_v3/moe/experts/base.py`
- Test: `tests/unified_v3_moe/test_expert_base.py`

**Interfaces:**
- `ExpertContext(semantic_observation, world, task_hypotheses, support_demonstrations, dialogue_state, metadata)`.
- Abstract `ExpertAdapter.propose(context) -> ExpertProposal`.
- `SafeExpertRunner.run(spec, adapter, context) -> ExpertProposal` catches timeout/schema/runtime failures and returns abstaining failed proposals.

- [ ] RED tests for exception, malformed proposal, disabled expert, and timeout behavior.
- [ ] Implement schema validation and fail-closed runner.
- [ ] GREEN focused tests.
- [ ] Commit `feat(v3-moe): add fail-closed expert adapter runtime`.

### Task 3: R7-L fast-induction adapter

**Files:**
- Create: `src/nexus_gllm/unified_v3/moe/experts/r7l_fast_induction.py`
- Test: `tests/unified_v3_moe/test_r7l_adapter.py`

**Interfaces:**
- Consumes support demonstrations encoded as `SupportMapping(state, execute_target, analyze_target)`.
- Produces latent operator mappings and `RuleHypothesis` proposals.
- Initial implementation supports the historical 4-state / two-intent R7-L contract and marks provenance `EXACT_HISTORICAL` only when the exact checkpoint hash is available; otherwise `ADAPTER_RECONSTRUCTION`.

- [ ] RED test reproducing a held-out permutation from three support states without weight update.
- [ ] RED test that no-support input abstains rather than guesses.
- [ ] Implement adapter preserving support/query separation.
- [ ] GREEN R7-L adapter tests.
- [ ] Commit `feat(v3-moe): add R7-L fast induction expert`.

### Task 4: R7.2 Russian operator binder adapter

**Files:**
- Create: `src/nexus_gllm/unified_v3/moe/experts/r72_language.py`
- Test: `tests/unified_v3_moe/test_r72_language.py`

**Interfaces:**
- Consumes Russian controlled operator demonstrations plus semantic IR.
- Emits operator binding/entity-role proposal and normalized support mapping.
- Delegates latent mapping induction to R7-L expert; R7.2 itself does not become answer authority.

- [ ] RED active/passive/reordered Russian fixtures.
- [ ] RED instruction/content disentanglement fixture.
- [ ] Implement adapter around existing v2 R7.2 donor contracts where possible.
- [ ] GREEN and verify old v2 donor tests remain unchanged if locally available.
- [ ] Commit `feat(v3-moe): add R7.2 language expert`.

### Task 5: Evidence, context, graph and v3 native experts

**Files:**
- Create: `src/nexus_gllm/unified_v3/moe/experts/r718_evidence.py`
- Create: `src/nexus_gllm/unified_v3/moe/experts/r744_context.py`
- Create: `src/nexus_gllm/unified_v3/moe/experts/omega15r2_graph.py`
- Create: `src/nexus_gllm/unified_v3/moe/experts/v3_hypothesis.py`
- Test: `tests/unified_v3_moe/test_primary_experts.py`

**Interfaces:**
- Evidence expert proposes claims/evidence confidence/conflict metadata.
- Context expert proposes active/superseded state and coreference bindings.
- Graph expert proposes typed subject/operator/object atoms with role confidence.
- v3 expert proposes candidate worlds/rules/tasks using existing P0.1 hypothesis machinery.

- [ ] RED tests for evidence conflict, temporal context revision, graph-role ambiguity, and v3 multi-hypothesis preservation.
- [ ] Implement typed wrappers; mark reconstructed donors honestly.
- [ ] GREEN focused suite + `tests/unified_v3`.
- [ ] Commit `feat(v3-moe): integrate primary proposal experts`.

### Task 6: Capability router features and heuristic baseline

**Files:**
- Create: `src/nexus_gllm/unified_v3/moe/capability_router.py`
- Test: `tests/unified_v3_moe/test_router.py`

**Interfaces:**
- `RouterFeatures` includes semantic/task/novelty/cost features only.
- `extract_router_features(context) -> RouterFeatures`.
- `HeuristicCapabilityRouter.route(features, registry, k_min=2, k_max=4) -> RoutingDecision`.

- [ ] RED feature-quarantine test ensuring benchmark/split/track/case/gold fields cannot enter feature vector.
- [ ] RED support-demonstration episode routes R7-L/R7.2.
- [ ] RED evidence conflict routes R7.18 + v3.
- [ ] Implement heuristic baseline used later as training comparator.
- [ ] GREEN.
- [ ] Commit `feat(v3-moe): add capability router baseline`.

### Task 7: Novelty gate

**Files:**
- Create: `src/nexus_gllm/unified_v3/moe/novelty_gate.py`
- Test: `tests/unified_v3_moe/test_novelty_gate.py`

**Interfaces:**
- `NoveltyState = KNOWN|UNCERTAIN|NOVEL`.
- `NoveltySignals(max_confidence, router_entropy, semantic_distance, ast_novelty, disagreement, support_available)`.
- `NoveltyGate.classify(signals) -> NoveltyDecision`.
- NOVEL decisions force inclusion of `r7l_fast_induction` when support exists and `v3_hypothesis` always.

- [ ] RED known/uncertain/novel boundary tests.
- [ ] RED novel-with-support widening.
- [ ] RED novel-without-support conservative abstention/widening.
- [ ] Implement deterministic baseline gate.
- [ ] GREEN.
- [ ] Commit `feat(v3-moe): add novelty-aware routing gate`.

### Task 8: Expert calibration and lineage-aware proposal fusion

**Files:**
- Create: `src/nexus_gllm/unified_v3/moe/calibration.py`
- Create: `src/nexus_gllm/unified_v3/moe/proposal_fusion.py`
- Test: `tests/unified_v3_moe/test_proposal_fusion.py`

**Interfaces:**
- `ExpertCalibrator.calibrate(expert_id, capability, raw_confidence, novelty_bucket) -> float`.
- `ProposalFusion.fuse(proposals, registry) -> FusedProposalSet`.
- Fusion computes task-fit/support/independence/contradiction/generalization/cost utility and emits accepted/competing facts/rules/tasks plus conflicts.

- [ ] RED majority-vote trap: two correlated lineage experts must not beat one independent strongly verified expert merely by count.
- [ ] RED irrelevant high-confidence expert must not change correct fused conclusion.
- [ ] RED conflict remains `CONFLICTED`/competing rather than last-write-wins.
- [ ] Implement lineage-aware utility.
- [ ] GREEN.
- [ ] Commit `feat(v3-moe): add calibrated lineage-aware fusion`.

### Task 9: MoE sovereign runtime

**Files:**
- Create: `src/nexus_gllm/unified_v3/moe/runtime.py`
- Test: `tests/unified_v3_moe/test_moe_runtime.py`
- Modify: `src/nexus_gllm/unified_v3/__init__.py` only to export the new runtime without changing P0 APIs.

**Interfaces:**
- `UnifiedNexusV3MoE.respond(context) -> MoEResponse`.
- Stages: front-end proposals -> router -> novelty gate -> SafeExpertRunner -> fusion -> v3 hypothesis/world commit -> executor -> counterfactual/generalization -> epistemic final.
- Trace records selected experts, shadow experts, failures, lineage weights, fusion decisions, final authority events.

- [ ] RED full episode exercising support demos + Russian binder + graph + evidence conflict.
- [ ] RED negative-transfer fixture where irrelevant expert is injected but final answer stays correct.
- [ ] RED removal-ablation where removing useful expert degrades/abstains.
- [ ] Implement orchestration.
- [ ] Run all MoE + existing v3 tests.
- [ ] Commit `feat(v3-moe): add sovereign MoE runtime`.

### Task 10: Shadow expert registry for remaining top NEXUS versions

**Files:**
- Create: `src/nexus_gllm/unified_v3/moe/experts/r76_semantic_memory.py`
- Create: `src/nexus_gllm/unified_v3/moe/experts/r78_formal.py`
- Create: `src/nexus_gllm/unified_v3/moe/experts/r710_proof.py`
- Create: `src/nexus_gllm/unified_v3/moe/experts/r714_morpholex.py`
- Create: `src/nexus_gllm/unified_v3/moe/experts/v10_procedural.py`
- Create: `src/nexus_gllm/unified_v3/moe/experts/unified_r13.py`
- Create: `src/nexus_gllm/unified_v3/moe/experts/v30_shadow.py`
- Test: `tests/unified_v3_moe/test_shadow_registry.py`

- [ ] RED registry test requiring these experts present as SHADOW unless exact artifact + calibration gate explicitly activates them.
- [ ] Implement conservative adapters/stubs that emit typed proposals or abstain, never fabricate historical capability.
- [ ] GREEN.
- [ ] Commit `feat(v3-moe): register remaining top NEXUS experts in shadow mode`.

### Task 11: Mixed expert-rollout training corpus

**Files:**
- Create: `training/v3_moe/__init__.py`
- Create: `training/v3_moe/episode.py`
- Create: `training/v3_moe/expert_rollout.py`
- Create: `training/v3_moe/utility.py`
- Create: `training/v3_moe/dataset.py`
- Test: `tests/v3_moe_training/test_dataset_utility.py`

**Interfaces:**
- Independent synthetic families `MOE-TRAIN-A`, `MOE-DEV-B`, `MOE-OOS-C`.
- Episodes span support induction, Russian operator binding, evidence conflict, context revision, graph roles, procedural/compositional reasoning, temporal/counterfactual novelty.
- Each episode stores scorer-side expert correctness and marginal contribution; model-visible router features omit expert outcome/gold/split identifiers.
- `marginal_utility(rollout, expert_id)` compares fused result with/without expert.

- [ ] RED train/dev/OOS namespace/topology separation.
- [ ] RED no-leak feature test.
- [ ] RED useful-expert positive marginal utility and harmful-expert negative utility.
- [ ] Implement generator/rollout dataset.
- [ ] GREEN.
- [ ] Commit `feat(v3-moe): add expert rollout training curriculum`.

### Task 12: Learned Top-K router

**Files:**
- Create: `training/v3_moe/router_model.py`
- Create: `training/v3_moe/train_router.py`
- Test: `tests/v3_moe_training/test_router_training.py`

**Interfaces:**
- PyTorch `CapabilityRouterNet(input_dim, expert_count)`.
- Multi-label utility target over experts.
- Loss combines useful-expert recall, harmful-expert suppression, expert-count cost and lineage redundancy penalty.
- Checkpoint selection uses MOE-DEV-B only.

- [ ] RED deterministic smoke-training test.
- [ ] RED learned router must beat random Top-K and heuristic baseline on MOE-OOS-C useful-expert recall.
- [ ] Implement seeded vectorized training.
- [ ] Train first full target corpus: at least 50k train / 5k dev / 5k OOS if runtime permits; otherwise label smaller run smoke.
- [ ] Persist checkpoint/config/metrics/hashes.
- [ ] Commit `feat(v3-moe): train cost-aware Top-K router`.

### Task 13: Learned novelty detector and calibration

**Files:**
- Create: `training/v3_moe/novelty_model.py`
- Create: `training/v3_moe/calibration.py`
- Test: `tests/v3_moe_training/test_novelty_calibration.py`

**Interfaces:**
- Novelty classifier predicts KNOWN/UNCERTAIN/NOVEL from allowed structural features.
- Per-expert calibrator learns probability correction on DEV only.
- Report AUROC, ECE, Brier, false-known rate.

- [ ] RED novelty smoke test and calibration-improves-ECE test.
- [ ] Train on TRAIN/DEV without OOS threshold tuning.
- [ ] Evaluate once on OOS.
- [ ] Persist artifacts/hashes.
- [ ] Commit `feat(v3-moe): train novelty and expert calibration`.

### Task 14: Mixed META-OOS evaluation and ablations

**Files:**
- Create: `training/v3_moe/evaluate.py`
- Output: `artifacts/v3_moe/p1/`
- Test: `tests/v3_moe_training/test_meta_oos_eval.py`

**Required comparisons:**
- best single expert;
- all experts;
- random Top-K;
- heuristic router;
- learned Top-K router;
- oracle router;
- learned router with lineage discount disabled;
- learned router with novelty gate disabled;
- learned router with R7-L removed.

**Metrics:**
- fused answer accuracy;
- best-single accuracy;
- MoE gain;
- useful-expert Top-K recall;
- negative-transfer rate;
- average active experts/query;
- calibration ECE/Brier;
- novelty AUROC;
- rename invariance;
- intervention sensitivity;
- per-capability accuracy.

- [ ] RED evaluator denominator/negative-transfer tests.
- [ ] Implement evaluator.
- [ ] Run OOS exactly after DEV-selected checkpoint freeze.
- [ ] Persist JSON metrics, manifests and hashes.
- [ ] Commit `test(v3-moe): record mixed META-OOS ablations`.

### Task 15: Verification and report

**Files:**
- Create: `docs/results/2026-09-18-nexus-v3-moe-p1-training-report.md`

- [ ] Run all existing `tests/unified_v3`.
- [ ] Run `tests/unified_v3_moe`.
- [ ] Run `tests/v3_moe_training`.
- [ ] Run `python -m compileall -q src/nexus_gllm/unified_v3 training/v3_moe`.
- [ ] Scan source/training features for benchmark/split/gold/renderer leakage.
- [ ] Verify all configured historical artifact hashes; report exact vs reconstructed provenance.
- [ ] Record router/novelty/calibration checkpoint SHA-256.
- [ ] Record training/dev/OOS sizes and all ablations.
- [ ] Explicitly report whether promotion gates pass:
  - MoE >= best single +5pp;
  - negative transfer <=2%;
  - useful-expert Top-K recall >=95%;
  - schema failures accepted =0;
  - hash-mismatch experts loaded =0;
  - rename invariance >=95%;
  - novelty AUROC >=0.90;
  - intervention sensitivity >=90%;
  - ECE <=0.10.
- [ ] Commit verification report only after fresh evidence.
