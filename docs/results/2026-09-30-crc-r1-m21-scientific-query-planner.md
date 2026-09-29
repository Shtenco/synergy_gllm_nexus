# CRC-R1 M21 — Information-Gain Scientific Query Planner

**Date:** 2026-09-30

M21 joins three previously separate CRC capabilities:

- M16 information-gain query selection;
- M15 causal/interventional reasoning;
- M13 external action authority.

A candidate observation/experiment can be selected because it is expected to reduce uncertainty, but selection produces only an immutable `ActionProposal`.

Read-only observations are tagged `READ_ONLY`. Interventions are tagged at least `MEDIUM` risk and therefore require explicit external approval under the M13 action boundary.

The scientific loop is now:

`uncertain hypotheses → expected information gain → best observation/intervention → ActionProposal → META-OS permit → external executor → observation → causal/belief update`.

Choosing an experiment and performing an experiment are deliberately different authority steps.
