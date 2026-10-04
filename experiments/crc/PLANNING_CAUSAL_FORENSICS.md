# CRC Planning + Causal Bottleneck Forensics

Status: **post-second-blind DEV evidence**. This document does not alter the historical second-blind verdict.

## Immutable evidence boundary

Second post-freeze blind authority:

- frozen cognitive SHA: `97a9c7ed12900969c68ba596e629c70adb398f06`
- run: `37143234492`
- artifact: `11280614978`
- digest: `sha256:9692af0ab08b663d14d358176c88facfe0b7b4eb8f6ee85f34d54789438c18d4`
- exact task success: `0.8458333333`
- planning family: `0.500`
- causal family: `0.575`
- historical mechanical verdict: `TRANSFER_SUPPORTED`

The result above is immutable. The cases may now be inspected only as DEV failure evidence; they may never be reused as later blind transfer evidence.

## Planning failure decomposition

The second-blind generator assigns

`horizon = 2 + ((seed + repeat) % 4)`

for eight consecutive seeds and ten repeats. Therefore the 80 planning cases are exactly balanced:

| Horizon | Cases |
|---|---:|
| H2 | 20 |
| H3 | 20 |
| H4 | 20 |
| H5 | 20 |

At the frozen SHA, `ComputeBudget.max_depth == 3`. `CognitiveLoopR1` passes `meta.branch_depth` directly to `LearnedFuturePlanner(max_depth=...)`; after the first FAR-OOS repair the meta controller authorizes the full budget maximum, but the maximum itself remains three.

Therefore:

- H2 and H3 terminal rewards are reachable;
- H4 and H5 terminal rewards are structurally unreachable;
- exactly half of the balanced H2-H5 family is beyond the planner search horizon.

The observed family score `40/80 = 0.500` is therefore explained by a hard architecture horizon, not by random value noise.

### Planning root cause

`fixed max_depth=3` is acting as a capability ceiling while the outer compute protocol charges the future module a flat cost. The system has no measured mapping

`compute budget -> expanded nodes -> reachable depth`.

The next DEV planner must therefore be budgeted and anytime rather than replacing `3` by another magic constant.

## Causal failure decomposition

The second-blind causal family constructs a sign-flipped observational/interventional conflict:

- observational support: `+/-0.75`
- interventional support: opposite sign, magnitude `0.88`
- counterfactual support: same sign as intervention, magnitude `0.82`
- blind oracle: abstain on the conflict.

At the frozen SHA, `CausalGraph.edge()` discards evidence polarity after a coarse split:

- every negative support, regardless of evidence kind, is accumulated into one `contradiction_mass`;
- only positive interventional/counterfactual support contributes to `causal` mass;
- the returned edge has no signed causal direction.

This creates sign-orientation asymmetry.

### Orientation A

Observation positive; intervention and counterfactual negative.

Both causal rows become generic contradiction mass, so the edge is not identified and the benchmark records success.

### Orientation B

Observation negative; intervention and counterfactual positive.

The observation becomes contradiction mass `0.75`, while causal mass is `0.88 + 0.82 = 1.70`. The frozen rule sees sufficient positive causal mass and identifies the edge, while the blind oracle expects abstention.

The observed `0.575` is therefore consistent with random orientation imbalance around a nominal 50/50 split.

### Causal root cause

There are two distinct issues and they must not be conflated:

1. **Architecture defect:** evidence polarity and evidence kind are collapsed, so the graph cannot represent a negative causal effect or distinguish disagreement among observation, intervention and counterfactual evidence.
2. **Benchmark semantic limitation:** the second-blind oracle treats observational/interventional sign conflict as automatic non-identifiability. For a genuinely confounded observational channel, strong agreeing intervention + counterfactual evidence can instead identify a causal effect despite opposite correlation. Therefore the historical 57.5% remains valid under its pre-registered oracle, but the next DEV causal benchmark must use an explicit structural causal oracle rather than optimize the architecture to this binary rule.

## DEV hypotheses

### P1 — Budgeted anytime planning

If search is priced by actual expansion work and iterative deepening is allowed up to an architectural safety cap, then planning accuracy should increase monotonically with available search budget and H4/H5 should become reachable without breaking H2/H3.

### C1 — Signed structural causal evidence

If causal evidence preserves signed interventional and counterfactual effects, then:

- correlation alone never identifies causality;
- agreeing intervention + counterfactual can identify either positive or negative effects;
- conflicting intervention vs counterfactual evidence abstains;
- observational disagreement does not by itself reverse a well-supported causal direction;
- random SCM evaluation can be scored against an independent do/counterfactual oracle.

## Required TDD gates

1. Add a planning RED suite before planner production changes.
2. Add a causal RED suite before causal production changes.
3. Preserve all historical benchmark/verdict documents.
4. Make the smallest architecture changes that close the RED contracts.
5. Run focused GREEN, controlled equal-budget regression, M32 evidence/CI, Windows variants where available, and full repository CI.
6. Only after all required regressions are green create a new commit-bound freeze.
7. Only after that freeze author a third fresh blind corpus.

## Seals

- `M32-META`: **SEALED / UNOPENED**
- `FTX2`: **UNAUTHORED**
