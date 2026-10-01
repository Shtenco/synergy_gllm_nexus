# NEXUS-MOE-B2 — hard far-OOS protocol freeze candidate

**Date:** 2026-09-30  
**Branch:** `crc-r1-foundation`

The base branch contained only an empty `benchmarks/moe_b2/__init__.py`. This milestone implements the actual B2 protocol but deliberately does **not** publish a learned P1 one-shot result before the frozen P1 runtime is executed.

## Purpose

B2 tests routing generalization under a distribution authored independently from the P1 synthetic router curriculum. It is a routing/generalization benchmark, not an AGI benchmark and not a substitute for end-to-end expert execution.

Six strata are frozen: `cross_capability`, `cue_conflict`, `open_set`, `cost_pressure`, `composition_shift`, and `adversarial_mixture`.

The generator uses nonlinear cross-capability interactions and far-OOS feature geometry rather than reusing the P1 utility law. Runtime records expose only case ID, eight routing features and stratum. Useful/harmful experts, utilities and abstention targets are scorer-only.

## Protocol

1. Generate runtime and scorer-only gold.
2. Persist both and freeze SHA-256 before routing.
3. Verify the seal.
4. Route every runtime case without scorer gold.
5. Persist routes.
6. Re-verify the seal.
7. Open scorer-only gold once and compute metrics.
8. Record `test_open_count=1`, `tuning_after_open=false`, `ftx1_used=false`, `hard_oos_d_reused=false`.

Metrics include useful-expert recall, harmful-selection rate, strict success, abstention accuracy and routing regret, with random and oracle controls.

## Verification

Local B2 protocol tests: **5 passed**. They verify scorer isolation, all six strata, unique IDs, mutation detection, oracle/random ordering and one-shot bookkeeping.

## Scientific boundary

No learned P1 B2 score is claimed in this commit. A score becomes publishable only after the exact frozen P1 router/calibrator/novelty artifacts execute against the sealed B2 runtime without post-open tuning.

FTX1 remains sealed.
