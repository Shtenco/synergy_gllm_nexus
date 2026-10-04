# CRC PRE-FAR-OOS ARCHITECTURE FREEZE

Status: **FROZEN FOR FAR-OOS EVALUATION**

Frozen architecture commit:

`6067746d3dbab7a5a0a7388545b73116fd23c25a`

The discriminative controlled-DEV benchmark at this commit established the cumulative behavioral staircase A→B→C→D→E under an equal compute budget. This freeze does **not** claim general transfer.

## Frozen architectural surface

For the FAR-OOS experiment, all implementation files under:

`src/nexus_gllm/unified_v3/cognitive/`

are commit-bound to the SHA above. FAR-OOS evaluator/corpus/workflow commits may be added after this freeze, but the frozen cognitive implementation may not change before the FAR-OOS verdict is recorded.

## Evaluation boundary

The upcoming FAR-OOS corpus must:

- be authored after this freeze;
- not reuse the controlled DEV case generator;
- use held-out entities, relations, causal structures, planning graphs and task compositions;
- include multi-step proof, causal intervention/counterfactual, long-horizon planning, memory retention/forgetting, cross-language labels/instructions where the structured contract permits them, unseen task-schema compositions, calibration/abstention, and post-feedback transfer;
- run the already frozen A/B/C/D/E stages without architecture tuning;
- report failures as failures rather than modifying the frozen implementation.

## Seals preserved

- `M32-META`: **SEALED / UNOPENED**
- `FTX2`: **UNAUTHORED**
- no V8/V9/M33 label is introduced

## Allowed post-freeze changes before verdict

Only evaluation-side material: FAR-OOS corpus, benchmark runner, tests validating benchmark integrity, workflow, result artifact, and verdict documentation.

Any change to `src/nexus_gllm/unified_v3/cognitive/` invalidates this freeze and requires a new explicit architecture selection/freeze before another FAR-OOS attempt.
