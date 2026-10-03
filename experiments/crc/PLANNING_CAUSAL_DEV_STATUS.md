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
- current DEV therefore uses signed interventional/counterfactual structural rules rather than tuning to the historical 57.5% number.

## New DEV contracts

Planning contracts:

- `tests/crc_r1/test_post_second_blind_planning_budget.py`
  - explicit transition expansion budget;
  - H5 reachability with sufficient expansions;
  - explicit budget exhaustion telemetry;
  - no loss of a solved short-horizon policy when more compute is available.
- `tests/crc_r1/test_post_second_blind_cognitive_loop_planning.py`
  - H8 planning through the full `CognitiveLoopR1`;
  - separate planning safety horizon reaches the planner through `MetaController`;
  - expansion cap is preserved through the production loop.

Causal contracts:

- `tests/crc_r1/test_post_second_blind_signed_causal.py`
  - positive/negative causal-effect symmetry;
  - opposite observational correlation cannot erase agreeing intervention + counterfactual evidence;
  - intervention/counterfactual disagreement abstains.

Statistics contract:

- `benchmarks/crc_statistics.py`
- `tests/crc_r1/test_crc_statistics.py`
- Wilson 95% implementation is pinned to independent numerical reference values for the future stricter blind gate.

## Stratified planning + causal DEV

`benchmarks/crc_planning_causal_dev/run.py`

Planning:

- H2-H8;
- branching 2-5;
- exact sampled discounted-reward oracle;
- expansion budgets 4/8/16/32/64;
- fresh cases, not second-blind cases.

Signed causal surface:

- graph sizes 4-10;
- confounded correlation;
- correlation-only;
- causal disagreement;
- intervention-only;
- fresh cases, not second-blind cases.

DEV gate:

- planning @ 64 expansions >= 0.95 overall;
- minimum H2-H8 planning accuracy @ 64 >= 0.90;
- aggregate planning accuracy non-decreasing over the preregistered expansion budgets;
- signed causal accuracy >= 0.95;
- causal false-identification rate == 0.

## Independent structural causal oracle

The causal line now also has an evaluator that is separate from production inference:

- `benchmarks/crc_scm_oracle.py`
- `tests/crc_r1/test_crc_scm_oracle.py`

It implements a deterministic linear SCM with:

- acyclic structural equations;
- topological evaluation;
- `do(X=x)` replacement of a structural equation;
- total interventional effect;
- signed total effect;
- counterfactual evaluation while holding exogenous state fixed.

The random SCM DEV battery is:

- `benchmarks/crc_scm_dev/run.py`
- `tests/crc_r1/test_crc_scm_dev.py`

It generates fresh DAGs with 4-10 variables and four regimes:

1. identified structural effect with observational reversal;
2. correlation-only zero structural effect;
3. intervention-only insufficient evidence;
4. intervention/counterfactual causal-evidence conflict.

The oracle is the independent `LinearSCMOracle`, not `CausalGraph`.

Random SCM DEV gate:

- signed identification accuracy >= 0.95;
- false-identification rate == 0;
- minimum regime accuracy >= 0.90;
- all graph sizes 4-10 represented.

## Production changes under test

- `LearnedFuturePlanner` has an explicit transition-expansion budget and anytime telemetry.
- `ComputeBudget` preserves legacy `max_depth=3` and adds separate planning fields:
  - `max_planning_expansions=64`
  - `max_planning_depth=12`
- `MetaController` uses the separate planning safety horizon only when `future_planning` is explicitly requested.
- `CausalGraph` preserves signed observational/interventional/counterfactual evidence and identifies a signed causal effect only when intervention and counterfactual agree.
- `CognitiveLoopR1` records planning expansion telemetry and signed causal telemetry.

## Isolated logic sanity check

Because GitHub runners are not currently being allocated, the new algorithms were also reproduced in an isolated calculation as a non-authoritative logic check. This does **not** replace repository pytest/CI.

Observed on the same planning generation rules:

| expansion cap | overall planning accuracy |
|---:|---:|
| 4 | 0.08333 |
| 8 | 0.67262 |
| 16 | 1.00000 |
| 32 | 1.00000 |
| 64 | 1.00000 |

At cap 16 and above every H2-H8 stratum reached 1.0 in that isolated calculation.

The isolated signed-causal calculation reached:

- accuracy: `1.0`;
- false identification: `0.0`.

These numbers are useful for catching obvious contract/algorithm mismatches only. They are **not GREEN evidence** until executed from the repository on an authorized runner.

## CI / runner blocker

Current GitHub Actions failures are **not valid test executions**.

Example generic CI at RED-contract commit `b158eaeaff02d89c2058337e31d4fcc19a8477fc`:

- run `37145204669`
- job `111267593784`
- `runner_id=0`
- `runner_name=""`
- `steps=[]`
- created, started and failed within ~3 seconds.

Example focused diagnostic run:

- run `37145860810`
- job `111269541314`
- `runner_id=0`
- `runner_name=""`
- `steps=[]`.

For comparison, the authoritative successful second blind actually received a GitHub-hosted runner:

- run `37143234492`
- job `111261820193`
- runner `GitHub Actions 1000025386`
- checkout/install/tests/benchmark/validation/artifact steps all executed.

Therefore current red check marks represent runner allocation/infrastructure failure before checkout or pytest. They are neither scientific RED evidence nor GREEN evidence.

The earlier statement that those failed Actions runs themselves proved the RED contracts was too strong. The new contracts are structurally incompatible with the pre-repair interfaces, but the repository-level executed RED -> GREEN chain remains unverified until compute is actually allocated.

## CI gate prepared

`.github/workflows/crc-planning-causal-dev.yml` now executes, once a runner is available:

1. new planning contracts;
2. full-loop H8 integration;
3. new signed causal contracts;
4. historical planning/causal regressions;
5. stratified planning+causal DEV surface;
6. independent SCM oracle tests;
7. random SCM DEV battery;
8. statistics reference tests;
9. compileall;
10. JSON evidence artifact upload.

## Third-blind protocol state

`experiments/crc/THIRD_BLIND_PREREGISTRATION.md` exists as **protocol only**.

Pre-registered target:

- 10 fresh seeds;
- 50 repeats;
- 8 families;
- 4000 scored evaluations;
- planning H2-H10 / branching 2-5 / stochastic traps;
- random SCM 4-10 nodes;
- six transfer-control families;
- Wilson 95% lower bound overall > 0.80;
- Wilson 95% lower bounds for Planning and Causal > 0.60;
- control-family point accuracy >= 0.80;
- zero budget violations;
- zero credit leakage.

No third-blind generator, seeds, corpus or answers have been authored.

## Freeze gate

A new commit-bound freeze is **BLOCKED** until all of the following are actually executed:

1. focused planning/causal tests GREEN;
2. full-loop H8 planning GREEN;
3. planning/causal DEV benchmark GREEN;
4. random SCM DEV GREEN;
5. old controlled equal-budget regression GREEN;
6. M32 evidence/CI GREEN on required platforms;
7. full repository `pytest -q` GREEN;
8. `compileall` GREEN.

Only then may a new frozen cognitive SHA be recorded and the third unseen blind generator/corpus be authored.

## Seals

- `M32-META`: **SEALED / UNOPENED**
- `FTX2`: **UNAUTHORED**
- third-blind generator: **UNAUTHORED**
- third-blind corpus: **NOT AUTHORED**
