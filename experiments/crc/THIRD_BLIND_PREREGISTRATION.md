# Third Fresh Transfer Blind — Pre-registration Only

Status: **PROTOCOL PRE-REGISTERED; CORPUS NOT AUTHORED**.

This file defines the future one-shot evaluation contract before the next architecture freeze. It intentionally contains no blind seeds, generated instances, reward graphs, SCM instances, answers, or corpus generator. Those may be authored only after a new commit-bound cognitive freeze is recorded.

## Scientific boundary

Historical evidence remains immutable:

1. first frozen FAR-OOS -> `PARTIAL_TRANSFER`;
2. second post-freeze blind -> `TRANSFER_SUPPORTED` at 84.5833% exact task success, with Planning=50% and Causal=57.5%.

The third blind exists to test whether the Planning + Causal repair transfers beyond the new DEV surfaces without sacrificing the four previously strong mechanisms.

## Corpus size

Target:

- 10 fresh seeds;
- 50 repeats per family per seed;
- 8 families;
- total scored evaluations = `10 * 50 * 8 = 4000`.

If Actions resource limits make 4000 impossible, the count may be reduced **before corpus generation and before execution**, with the revised count committed in a separate protocol-only commit. It may not be changed after seeing any blind result.

## Families

The future generator must create fresh instances for eight roles. Names may be implemented literally or equivalently, but semantic roles are frozen here.

1. `PLANNING_STOCHASTIC_H2_H10`
   - horizons 2 through 10;
   - branching factors 2 through 5;
   - exact per-edge sampled rewards;
   - delayed positive and negative outcomes;
   - local reward traps;
   - irreversible branches;
   - stochastic transitions where an independent oracle can enumerate/DP expected return;
   - no reused second-blind planning instances.

2. `CAUSAL_RANDOM_SCM`
   - 4 through 10 observed nodes;
   - signed direct effects;
   - observational confounding/reversal;
   - intervention and counterfactual evidence;
   - missing evidence and conflicting causal evidence;
   - irrelevant edges;
   - independent SCM oracle, not `CausalGraph` itself.

3. `MEMORY_DISTRACTOR_BRIDGE`
   - fresh provenance-backed bridge facts;
   - many ungrounded distractors;
   - no blind fact may have appeared in DEV.

4. `PROGRAM_NESTED_TRANSFER`
   - fresh nested control/program structures;
   - combinations of composition, temporal constraints and inhibition/counterfactual operators where supported by the frozen language.

5. `CREDIT_MULTI_EPISODE_SHIFT`
   - fresh candidate identities;
   - multi-episode feedback;
   - distractor memory/program nodes;
   - zero credit leakage to ineligible nodes.

6. `META_RESOURCE_CALIBRATION`
   - mixed easy/hard cases;
   - variable uncertainty/novelty;
   - correct answer vs abstention oracle;
   - compute-budget compliance.

7. `CROSS_LANGUAGE_COMPOSITION`
   - fresh multilingual surface forms mapped to the same typed task semantics;
   - no reuse of prior blind prompts.

8. `UNSEEN_TASK_SCHEMA_COMPOSITION`
   - fresh schema combinations within the frozen admitted task language;
   - independent semantic oracle;
   - no post-result architecture tuning.

## Planning compute axis

The blind must record at minimum:

- requested planning horizon;
- realized plan depth;
- branching factor;
- expansion cap;
- expanded nodes;
- budget exhausted flag;
- oracle root action;
- chosen root action;
- expected-return regret where defined.

A blind case is not allowed to change architecture configuration after inspecting its answer.

## Causal metrics

Record at minimum:

- identification accuracy;
- signed-effect accuracy;
- false-identification rate;
- abstention precision/recall when oracle says non-identifiable;
- graph size;
- evidence regime;
- intervention/counterfactual agreement status.

## Confidence intervals

Use a two-sided Wilson score interval with 95% confidence (`z = 1.959963984540054`) for binomial success metrics.

For `k` successes in `n` trials, the lower bound is:

```
p = k / n
D = 1 + z^2 / n
center = (p + z^2 / (2n)) / D
radius = z * sqrt(p(1-p)/n + z^2/(4n^2)) / D
lower = center - radius
```

The implementation must be tested against an independent numerical reference before the blind is executed.

## Pre-registered transfer verdict

`TRANSFER_SUPPORTED` requires **all** of the following:

1. Wilson 95% lower bound for overall exact task success is strictly greater than `0.80`;
2. Wilson 95% lower bound for `PLANNING_STOCHASTIC_H2_H10` is strictly greater than `0.60`;
3. Wilson 95% lower bound for `CAUSAL_RANDOM_SCM` is strictly greater than `0.60`;
4. each of the six control families has point accuracy at least `0.80`;
5. `budget_violations == 0`;
6. `credit_leakage == 0`;
7. protocol seals report `m32_meta_opened == false` and `ftx2_authored == false`.

`PARTIAL_TRANSFER` applies when the strict transfer gate fails but overall point exact task success is at least `0.50`.

Otherwise the verdict is `FAIL`.

The verdict is mechanical. No threshold may be changed after any third-blind case has been evaluated.

## Freeze-before-authoring rule

The sequence is mandatory:

```
Planning+Causal DEV GREEN
        -> old regressions GREEN
        -> full CI GREEN
        -> commit-bound cognitive FREEZE
        -> freeze guard committed
        -> only then author third-blind generator/corpus
        -> one-shot execution
        -> immutable verdict
```

No third-blind generator, seeds or case corpus are authorized before that freeze.

## Post-blind rule

If the third blind is `FAIL` or `PARTIAL_TRANSFER`, preserve it unchanged and start a new DEV cycle using failure analysis only. The same corpus may never become fresh blind evidence again.

If it is `TRANSFER_SUPPORTED`, that still does not establish universal AGI. It supports transfer on the pre-registered families/population only.

## Seals

- `M32-META`: **SEALED / UNOPENED**
- `FTX2`: **UNAUTHORED**
- third-blind generator: **UNAUTHORED**
- third-blind seeds: **UNSELECTED / UNCOMMITTED**
