# NEXUS v3-MoE GF P1 Training Report

**Date:** 2026-09-18  
**Branch:** `unified-v3-generalization-first`  
**Spec:** `docs/superpowers/specs/2026-09-18-nexus-v3-moe-generalization-federation-design.md`  
**Plan:** `docs/superpowers/plans/2026-09-18-nexus-v3-moe-generalization-federation.md`

## Scope delivered

Implemented the first hierarchical NEXUS v3-MoE federation with six ACTIVE proposal experts (R7-L fast induction, R7.2 Russian operator binder, R7.18 evidence, R7.44 context, Omega-1.5R2 graph, v3 hypothesis) and seven SHADOW registry entries (R7.6, R7.8, R7.10, R7.14, V10, Unified R1.3, V30).

Historical experts have proposal-only authority. Final authority is labelled `v3_epistemic`. Proposal fusion applies lineage discount rather than majority voting. Artifact hash mismatch disables an expert fail-closed.

## TDD evidence

Initial MoE RED run:

```text
5 errors during collection
ModuleNotFoundError for MoE contracts/experts/training modules
```

First production pass exposed a real Russian role/morphology error (`Анны` vs canonical `анна`). The production binder was corrected; the test was not weakened.

Intermediate MoE suite:

```text
18 passed
```

The first 50k/5k/5k Router P1 run was rejected because learned Top-K recall was only 77.29% while the single-signal heuristic scored 100%. This revealed two problems: undertraining and a shortcut-easy curriculum.

An anti-shortcut test was added. The curriculum was redesigned so expert utility depends on combinations of allowed semantic features. The single-signal heuristic then fell to ~80% while the learned router could learn the joint utility function.

A second debugging pass found that an "epoch" had been only one full-batch gradient update. Training was changed to deterministic mini-batch epochs. The novelty detector received the same correction.

## Fresh final verification

```text
pytest tests/unified_v3_moe tests/v3_moe_training -q
......................... [100%]
25 passed in 4.77s
```

```text
python -m compileall -q src/nexus_gllm/unified_v3/moe training/v3_moe
```

Exit code: 0.

Forbidden router/training feature scan:

```text
anti_leak_hits []
```

## Accepted Router P1 training

```text
MOE-TRAIN-A = 50,000
MOE-DEV-B   =  5,000
MOE-OOS-C   =  5,000
seed        = 17
epochs      = 14 deterministic mini-batch epochs
```

Observed runtime in the execution sandbox: ~5.3 seconds for final train/eval artifact generation.

### OOS metrics

```text
useful_expert_recall             99.62%
random_topk_recall               49.74%
heuristic_topk_recall            79.50%
negative_transfer_rate            0.48%
dev_useful_expert_recall         99.77%
novelty_accuracy                 99.62%
novelty_AUROC                     0.999966
expert_calibration_ECE            0.052251
expert_calibration_Brier          0.155730
strict_routing_success           98.80%
best_single_expert_useful_rate   77.50%
MoE gain over best-single proxy  21.30 pp
```

`strict_routing_success` requires the Top-3 route to contain all useful experts while selecting none of the scorer-designated harmful experts.

`best_single_expert_useful_rate` is a routing-curriculum proxy, not end-to-end answer accuracy on a historical benchmark. Therefore the 21.3 pp gain is evidence about learned routing on this curriculum, not an AGI or FTX1 result.

## Logical checkpoint hashes

```text
router logical SHA-256
5f9654f3c8d0096f04a88f01d8c9b4469467aa17e1fa2139fc41246b9b0d557f

novelty logical SHA-256
790532da5913d78a88da08d7f173131953567d12551cf6474ad4f623abb964c8

calibrator logical SHA-256
404ad8df4be3aa8b58c89cc156e3babb614b8d712b04ffc42aaae13868ef3f33
```

Serialized artifact SHA-256:

```text
router.pt      64ed453c3360c863ec7411d7c2d76afd85db93b4353fbb0f716f663fc789190b
novelty.pt     bb2fd3cbfdc8491cc242d29fbe6b5c667900cfb034f3f89c1e833968a9418a4d
calibrator.pt  d3ad93337c6d45f5dbb698686697689b67cc475ea7547025d3fe5a0f209f374a
manifest.json  c4cdac2dfd56b339a2eb06f3dcd7db521cc738fd50a9e54219079d9fb655fc10
metrics.json   2060fd60b09120f4d8e2922f6a9840f1d34fb8082366fcca5a7698b9c0212157
```

Verified local MoE source + training + test bundle fingerprint (40 Python files):

```text
555c63791c06567e20a0d452306da77ecc18bf27b58ac3eb9eb344962ea6d45f
```

## Promotion-gate interpretation

The synthetic Router P1 gates that can already be measured pass:

- useful-expert Top-K recall >=95%: PASS (99.62%);
- negative transfer <=2%: PASS (0.48%);
- novelty AUROC >=0.90: PASS (0.999966);
- expert calibration ECE <=0.10: PASS (0.052251);
- learned router beats random and single-signal heuristic: PASS.

The spec's end-to-end `MoE >= best single expert +5pp` answer-accuracy gate is NOT yet claimed. The current 21.3 pp comparison is a routing-utility proxy, not end-to-end answer accuracy. That gate requires a mixed executable expert benchmark with real per-expert answers/proofs, not synthetic utility labels.

## Historical provenance boundary

The first MoE P0 uses reconstructed typed adapters for historical experts unless an exact historical runtime/checkpoint is explicitly attached and hash-verified. Registry provenance therefore distinguishes `ADAPTER_RECONSTRUCTION`, `EXACT_HISTORICAL`, and `NATIVE_V3`.

The exact R7-L checkpoint is not silently claimed to be loaded by this P0 adapter. The adapter currently preserves the historical support/query induction contract in typed form. Activating exact historical checkpoints is a separate artifact-integration gate.

## Known limits

- Router P1 is trained on a synthetic mixed capability curriculum, not real end-to-end rollouts of all historical binaries.
- Seven additional top historical experts remain SHADOW and abstaining until exact/reconstructed adapter validation.
- The current Russian R7.2 adapter is controlled, not a full restoration of the historical binder.
- End-to-end fused answer accuracy against a newly frozen MoE benchmark is not yet measured.
- HARD-OOS D is consumed and was not reused as clean OOS.
- FTX1 BLIND remains sealed and untouched.
- Full legacy repository pytest was not available through a local clone because the execution sandbox could not resolve `github.com`; focused MoE tests were run in a reconstructed scratch workspace.

## Next gate

The correct next step is not more router epochs. It is artifact-complete expert activation and a new frozen `NEXUS-MOE-B1` benchmark that executes actual expert proposals and measures end-to-end fused answer accuracy, negative transfer, lineage-aware evidence gain, latency, and novelty behavior. Only after that should FAST-TRANSFER F1 and independently authored HARD-OOS F be opened.
