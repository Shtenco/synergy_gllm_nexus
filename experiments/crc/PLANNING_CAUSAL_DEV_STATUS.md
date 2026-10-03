# Planning + Causal Bottleneck Closure — DEV Status

This record is post-second-blind development evidence. It does not modify either historical blind verdict.

## Immutable historical evidence

- first FAR-OOS: `PARTIAL_TRANSFER` — immutable
- second post-freeze blind: `TRANSFER_SUPPORTED` — immutable
- second-blind run: `37143234492`
- second-blind artifact: `11280614978`
- second-blind digest: `sha256:9692af0ab08b663d14d358176c88facfe0b7b4eb8f6ee85f34d54789438c18d4`
- frozen second-blind cognitive authority: `97a9c7ed12900969c68ba596e629c70adb398f06`

The consumed second-blind workflow is now manual-only. Its historical evidence must not be replaced by later reruns.

## Forensics

Forensics authority: `experiments/crc/PLANNING_CAUSAL_FORENSICS.md`.

Planning:

- balanced H2/H3/H4/H5 second-blind family: 20 cases per horizon;
- frozen planning ceiling: depth 3;
- observed planning accuracy: 40/80 = 0.500;
- H4/H5 were structurally beyond the frozen search horizon.

Causal:

- frozen representation collapsed sign and modality into coarse mass/contradiction fields;
- negative causal effects could not be identified symmetrically;
- the consumed blind oracle also encoded an intentionally conservative but semantically limited rule: observational/interventional sign conflict => abstain;
- next DEV therefore uses signed interventional/counterfactual structural rules rather than tuning to the historical 57.5% number.

## New DEV contracts

Planning RED contract:

- `tests/crc_r1/test_post_second_blind_planning_budget.py`
- requires expansion telemetry, H5 reachability with sufficient expansions, explicit exhaustion, and non-regression with more compute.

Causal RED contract:

- `tests/crc_r1/test_post_second_blind_signed_causal.py`
- requires positive and negative causal-effect symmetry and abstention when intervention and counterfactual disagree.

Stratified DEV surface:

- `benchmarks/crc_planning_causal_dev/run.py`
- planning H2-H8;
- branching 2-5;
- exact sampled discounted-reward oracle;
- expansion budgets 4/8/16/32/64;
- fresh cases, not second-blind cases;
- causal graph sizes 4-10;
- confounded correlation, correlation-only, causal disagreement, intervention-only regimes;
- independent causal regime oracle;
- seals `M32-META=False`, `FTX2=False`.

DEV gate:

- planning @ 64 expansions >= 0.95 overall;
- minimum H2-H8 planning accuracy @ 64 >= 0.90;
- aggregate planning accuracy non-decreasing over the preregistered expansion budgets;
- signed causal accuracy >= 0.95;
- causal false-identification rate == 0.

## Production changes under test

- `LearnedFuturePlanner` has an explicit transition-expansion budget and anytime telemetry.
- `ComputeBudget` preserves legacy `max_depth=3` and adds separate planning fields:
  - `max_planning_expansions=64`
  - `max_planning_depth=12`
- `MetaController` uses the separate planning safety horizon only when `future_planning` is explicitly requested.
- `CausalGraph` preserves signed observational/interventional/counterfactual evidence and identifies a signed causal effect only when intervention and counterfactual agree.
- `CognitiveLoopR1` records planning expansion telemetry and signed causal telemetry.

## CI / runner blocker

Current GitHub Actions failures are **not valid test executions**.

Example generic CI at RED-contract commit `b158eaeaff02d89c2058337e31d4fcc19a8477fc`:

- run `37145204669`
- job `111267593784`
- `runner_id=0`
- `runner_name=""`
- `steps=[]`
- created, started, and failed within ~3 seconds.

Example focused diagnostic run at current DEV line:

- run `37145860810`
- job `111269541314`
- `runner_id=0`
- `runner_name=""`
- `steps=[]`

Therefore these failures show runner allocation/infrastructure failure before checkout or pytest. They are neither scientific RED evidence nor GREEN evidence.

The earlier statement that the Actions failures themselves proved the RED contracts was too strong; the RED contracts are justified by static mismatch with the prior interfaces, but a genuine executed RED/GREEN transition still requires an allocated runner or another authorized execution host.

## Freeze gate

A new commit-bound freeze is **BLOCKED** until all of the following are actually executed:

1. focused planning/causal tests GREEN;
2. planning/causal DEV benchmark gate GREEN;
3. old controlled equal-budget regression GREEN;
4. M32 evidence/CI GREEN on required platforms;
5. full repository `pytest -q` GREEN;
6. `compileall` GREEN.

Only then may a new frozen cognitive SHA be recorded and a third unseen blind authored.

## Seals

- `M32-META`: **SEALED / UNOPENED**
- `FTX2`: **UNAUTHORED**
- third blind corpus: **NOT AUTHORED YET**
