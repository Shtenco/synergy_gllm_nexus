# CRC-R1 M20 — Frozen Anti-Forgetting Replay Bank

**Date:** 2026-09-30

M7 could reject a candidate when given a regression count, but it did not define where that count came from. M20 makes the source of anti-forgetting evidence explicit.

A `FrozenReplayBank` contains immutable replay cases with:
- case ID;
- capability;
- payload SHA-256;
- baseline correctness;
- baseline confidence.

The bank has a deterministic manifest SHA. Candidate evaluation requires complete case coverage and reports:
- baseline/candidate accuracy;
- regressions (baseline correct → candidate wrong);
- corrections (baseline wrong → candidate correct);
- calibration delta;
- replay manifest SHA.

A bridge converts the report into the existing M7 `PromotionCandidate`. Thus a candidate that gains new skills but breaks one frozen capability is rejected under the default zero-regression gate.

This closes the provenance chain:
`frozen replay cases → measured regressions → promotion decision`.
