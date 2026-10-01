# CRC-R1 M5b — Learned Future Prediction

**Date:** 2026-09-30

M5b removes the strongest simplification in the original Future Tree scaffold: the planner no longer requires an externally perfect branch evaluator.

## Added components

### EmpiricalWorldModel
Learns from observed tuples:
`(state, action, next_state, reward)`.

For each state/action it stores:
- empirical next-state distribution;
- expected reward;
- sample count;
- transition uncertainty.

Unknown actions return maximum uncertainty rather than fabricated predictions.

### LearnedFuturePlanner
Future Tree branches now query the learned world model. Branch selection accumulates discounted predicted reward through ancestry and penalizes model uncertainty.

## Benchmark
Synthetic environments contain a deliberately misleading choice:
- `safe` gives immediate positive reward;
- `invest` gives a small immediate cost but unlocks a larger delayed reward.

Depth-1 planning is therefore myopic by construction. Depth-3 can exploit learned transition structure.

The benchmark is intentionally small and synthetic. It tests whether the mechanics of learned multi-step prediction work; it does not demonstrate real-world planning competence.

## Next
M6 will connect actual branch outcomes to the Cognitive Credit Graph so router/memory/program/branch reliability can update from prediction error rather than only be logged.
