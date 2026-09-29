# CRC-R1 M10a.1 — Cognitive Trace / Reward-Semantics Fix

Self-audit before integrated META-OOS found two errors in the first Cognitive Loop wiring.

## Fixed

### 1. Memory credit topology
Retrieved memories were accidentally connected as an ordered chain. That would make later retrieved memories look causally downstream of earlier ones and distort recursive credit.

They are now parallel contributors:

`meta → memory_i → program`

for every retrieved memory, with no memory-to-memory edge.

### 2. Planning value vs episode predicted reward
A branch planner's predicted return is not automatically the same quantity as the episode's external/task reward. M10a incorrectly copied `plan.value` into `state.predicted_reward`.

The request now carries an explicit `predicted_outcome_reward`. Planning value remains branch metadata only. RPE therefore compares like with like.

These fixes are made before any integrated META-OOS result is opened.
