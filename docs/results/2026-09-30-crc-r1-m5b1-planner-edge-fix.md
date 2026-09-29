# CRC-R1 M5b.1 — Future Planner Edge-Attribution Fix

Self-audit found an important planning bug before credit learning was connected: beam ranking must score the observed/predicted transition from the parent state and selected action. Re-evaluating the same action from the already reached child state assigns reward to the wrong edge.

The planner is therefore simplified to an explicit bounded beam search whose node stores cumulative discounted value. Each edge uses:

`Q_edge = gamma^(depth-1) * (E[reward | parent_state, action] - lambda * uncertainty)`.

This patch is deliberately committed before M6 so prediction error and recursive credit are not trained against a mis-attributed planner.
