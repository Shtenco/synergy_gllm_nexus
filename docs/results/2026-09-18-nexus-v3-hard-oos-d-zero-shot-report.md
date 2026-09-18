# NEXUS v3 HARD-OOS D Frozen Zero-Shot Report

**Date:** 2026-09-18  
**Branch:** `unified-v3-generalization-first`  
**Design commit:** `955744ed16a33cb33161a1650bfabb850433c599`  
**Plan commit:** `abb8ce9dcb844aea5eea1a39e9e8f0c1c7e30644`  
**Implementation/evaluation commit:** `392bac85448c321e9d84092f0583a11037065e35`

## Protocol

HARD-OOS D was constructed as an independent generator under `training/v3_hard_oos_d/`.

The D generator does not import `training.v3_meta.universe`. The frozen P0.1 checkpoint was verified before sealing and again before final publication.

Frozen checkpoint SHA-256:

```text
95fd54d5036c7dfda0da1b9edbff5b804e6fa7163aab2fec83459075eb3b2c96
```

No optimizer, gradient update, backward step, fit call, threshold tuning, or D-informed feature modification occurred between D sealing and zero-shot evaluation.

FTX1 BLIND was not accessed.

## TDD evidence

The initial HARD-OOS D test run was RED:

```text
9 errors during collection
ModuleNotFoundError: training.v3_hard_oos_d
```

After implementation:

```text
11 passed
```

A full regression run initially exposed a pytest module-name collision between two `test_generator.py` files. Only the HARD-D test filename was renamed; production behavior was unchanged.

Fresh final verification:

```text
pytest tests/unified_v3 tests/v3_meta tests/v3_hard_oos_d -q
............................................ [100%]
44 passed in 4.45s
```

```text
python -m compileall -q src/nexus_gllm/unified_v3 training/v3_meta training/v3_hard_oos_d
```

Exit code: 0.

Scans:

```text
hard_d_independence_scan=PASS
hard_d_zero_shot_update_scan=PASS
checkpoint_sha=95fd54d5036c7dfda0da1b9edbff5b804e6fa7163aab2fec83459075eb3b2c96
```

## Sealed HARD-OOS D corpus

Total episodes:

```text
10,000
```

Strata:

```text
novel_ast             2,000
partial_noisy         1,500
binding_ambiguity     1,500
temporal_inhibitor    1,500
counterfactual_traps  1,500
mixed_adversarial     2,000
```

Canonical corpus SHA-256:

```text
251a18ee0c1f92f40a547794ea6e4be7c698c9bb5ecd6f2f9b0f7b09df19c8f2
```

Sealed manifest SHA-256:

```text
265412782ccd25e9832bbfad962524ee11bedfe95ff15749e5cde7dea6549cc1
```

Topology inventory SHA-256:

```text
b1c9fbe602bb2f70a7410b85855f031fdeefccc99fa9cfac2162de790c5e79e2
```

Source + HARD-D test bundle SHA-256:

```text
ea29049a2694aa3e0ec2074d031a8d987d7b079c0e060fe437ceef7fb90f9b2c
```

## Frozen zero-shot result

The frozen P0.1 ranker was evaluated once after sealing.

Overall:

```text
hypothesis_ranking_accuracy  21.91%
answer_accuracy              21.91%
representation_failure_rate 100.00%
calibration_ECE              48.60%
AST topology exact            0.00%
AST topology partial          0.00%
counterfactual_accuracy       0.00%
temporal_accuracy             0.00%
inhibitor_accuracy            0.00%
theory_revision_score         0.00%
```

The zero values for AST/counterfactual/temporal/inhibitor metrics reflect a genuine representation failure of the frozen P0.1 system: the current learned ranker only scores the old eight compatibility channels and the current symbolic rule representation does not contain the new HARD-D AST program space. These cases are not removed from denominators.

## By stratum

```text
binding_ambiguity     24.67%
counterfactual_traps  19.00%
mixed_adversarial     18.20%
novel_ast             24.50%
partial_noisy         25.47%
temporal_inhibitor    20.00%
```

Every stratum has `representation_failure_rate = 100%` at the full AST representation level.

## Baselines

```text
random               11.94%
always_transitive    12.50%
simplicity            8.69%
contradiction-only   22.09%
explained-only       23.46%
frozen learned       21.91%
```

The frozen learned ranker does **not** beat the strongest simple baseline on HARD-OOS D.

It trails explained-only by 1.55 percentage points and is effectively in the same regime as contradiction-only.

## Interpretation

This is a falsification result, not a failed experiment.

P0.1's 99.44% META-OOS C score did not transfer to a generator with materially different latent program topology.

The main failure is deeper than ordinary prediction noise:

1. the ranker learned useful combinations of the original eight structural channels;
2. those channels are insufficient to represent novel D AST structure;
3. the symbolic engine also lacks the complete higher-order AST execution space required by D;
4. therefore the system cannot recover composition + state gate + inhibitor + temporal/counterfactual programs zero-shot;
5. confidence remains too high despite the shift, producing poor calibration.

The key bottleneck is now specifically:

```text
FIXED HYPOTHESIS REPRESENTATION / FIXED RULE BASIS
```

rather than merely insufficient training epochs.

## Scientific consequence

Training the current 8-feature ranker longer on A/B/C is not the next useful step.

The next architecture/training phase should introduce a compositional program representation and train proposal/ranking over AST structure itself.

A natural next training family is META-TRAIN E, derived from the *classes* of failures observed here but not by replaying D as an OOS exam.

Candidate E curriculum:

- variable-length AST encoder;
- graph/tree representation of rule programs;
- heterogeneous operator composition;
- state gates and inhibitors;
- temporal rule nodes;
- exception/override nodes;
- counterfactual intervention nodes;
- ambiguous-world beam supervision;
- explicit abstention/calibration objective;
- curriculum from single AST node to 2-5 level program trees.

After E training, HARD-OOS D must not be used as a clean OOS claim again. A new independently authored HARD-OOS F is required.

## Consumption status

HARD-OOS D is now consumed.

`artifacts/v3_hard_oos_d/consumed.json` records:

```text
consumed = true
```

Any future D-informed training or tuning invalidates D as an OOS benchmark by construction.

## Artifact hashes

```text
zero_shot_metrics.json
8b0f4ccb320c5a2a09a09a03b4f75f6a9c1a047944d4474d24cc09eb23d70814

baseline_metrics.json
7cc1b1bd4f66098bb38f7241e918a3acccea1f78eefa7557e49cfcf356b95b6c

consumed.json
8308ab6ef0261772d6d589b2704e059ee62dceee026979ffa73c6d5bc8c250f9
```
