# NEXUS Unified v3 P0.1 Hypothesis Engine + Synthetic Training Report

**Date:** 2026-09-18  
**Branch:** `unified-v3-generalization-first`  
**Parent checkpoint:** `e75aec5b7266876171ca30964309c99afe58283c`  
**Design commit:** `15b7b5195cd7fd27303c775a39c1bae0c51db5ce`  
**Plan commit:** `f2c285010b1c5abd246e5418e8bc2a8fbfc83113`  
**Implementation/training commit:** `d87d91ab7e5fc8498a642f1c59c7052412bcdef2`

## Implemented scope

P0.1 adds typed hypothesis state, bounded hypothesis beam search, rule algebra, prediction outcomes, temporal revisions, structured conflicts, counterfactual world cloning, richer task opcodes, symmetric/inverse/compositional execution support, weighted epistemic consensus, hypothesis-stability auditing, P0.1 runtime orchestration, disjoint synthetic meta-training families, anti-shortcut baselines, and a learned structural hypothesis ranker.

All prior P0 tests remain present and were rerun unchanged.

## TDD evidence

Fresh P0 baseline before P0.1:

```text
16 passed in 0.09s
```

The first P0.1 test run was RED:

```text
10 errors during collection
ModuleNotFoundError for the new hypothesis/rule/temporal/counterfactual/training modules
```

After implementation:

```text
32 passed in 4.54s
```

After vectorizing the ranker:

```text
32 passed in 1.70s
```

## Rejected easy training run

The first 50k/5k/5k corpus was rejected as scientifically too easy because both the learned ranker and the single-feature `explained-only` baseline achieved 100% OOS.

A new anti-shortcut regression test was added:

- explained-only OOS must be < 75%;
- the learned ranker must beat it by > 8 percentage points.

The test failed before the generator correction exactly because the baseline was 1.0.

The generator was then changed to use overlapping evidence channels so no single scalar feature solves the task.

## Fresh final verification

```text
python -m compileall -q src/nexus_gllm/unified_v3 training/v3_meta
```

Exit code: 0.

Anti-leak scan over v3 source and training source:

```text
anti_leak_scan=PASS
```

Final focused test suite:

```text
pytest tests/unified_v3 tests/v3_meta -q
................................. [100%]
33 passed in 1.83s
```

## Accepted first training pass

```text
python -m training.v3_meta.train \
  --output-dir artifacts/v3_meta/p01_first_hard \
  --train-episodes 50000 \
  --dev-episodes 5000 \
  --oos-episodes 5000 \
  --seed 17 \
  --epochs 16
```

Observed wall time in the execution sandbox: approximately 6.92 seconds.

Generator families are disjoint:

```text
META-TRAIN = A
META-DEV   = B
META-OOS   = C
```

META-OOS was evaluated after training. FTX1 BLIND was not accessed.

### Metrics

```text
train_accuracy             0.9950
dev_accuracy               0.9952
oos_accuracy               0.9944
dev_initial_accuracy       0.0940
oos_simplicity_baseline    0.2564
oos_explained_baseline     0.4274
generalization_gap         0.0006
```

The learned ranker beats the explained-only OOS baseline by 56.70 percentage points and the simplicity baseline by 73.80 points on this synthetic curriculum.

These numbers describe this synthetic curriculum only. They are not FTX1 results and are not evidence of general AGI capability.

## Checkpoint hashes

```text
ranker.pt
95fd54d5036c7dfda0da1b9edbff5b804e6fa7163aab2fec83459075eb3b2c96

manifest.json
fdd8ab3346e6a4f8d6004fbd99d8f6d8cc086425d2a9f89e51784d28a6f71b1f

metrics.json
5512866a06eb18ef3ace4fd0d205bc62e31d2885f8ca901fc7b05ab8d0af3dbf
```

Verified local Python source+test bundle fingerprint (43 Python files):

```text
4d5ff0a0d2dc12730091bf1d4d4e2dea1119d39f3866ebd3ef9dfaf1e8282856
```

## Scientific interpretation

P0.1 now demonstrates a bounded competing-hypothesis loop: multiple rule hypotheses can survive underdetermined evidence, discriminating evidence changes ranking, predictions can be confirmed/refuted, temporal corrections preserve history, conflicts remain explicit, and counterfactual intervention occurs on cloned worlds.

The learned component is deliberately subordinate to symbolic contracts: it ranks structural hypothesis candidates and does not generate final answers.

## Known limits

- The learned model is a small structural ranker, not a learned language encoder.
- The synthetic rule family set is still compact.
- META-OOS uses a disjoint family namespace/configuration but the same high-level generator implementation.
- Conditional/blocker/temporal execution semantics are only partially expanded compared with the full P0.1 design.
- The 99.44% OOS result indicates the next curriculum should be harder, not that training should simply be longer.
- FTX1 BLIND remains sealed.

## Next scientific gate

Increase distribution distance with a separately authored generator family D, held-out rule AST topologies, noisy/partial demonstrations, adversarial distractors, ambiguous bindings, multi-operator conditional/blocker compositions, and ablations comparing the learned proposal/ranking policy against the symbolic hypothesis search.
