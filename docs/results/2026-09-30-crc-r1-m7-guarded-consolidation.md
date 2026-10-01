# CRC-R1 M7 — Guarded Consolidation / Promotion Gate

**Date:** 2026-09-30

M7 turns the earlier three-speed continual-learning policy into an explicit promotion protocol for SLOW changes.

A neural/core/router candidate may be promoted only when all of the following are simultaneously true:
- immutable artifact SHA-256 is present;
- provenance is complete;
- replay suite passed;
- task score does not regress beyond the preregistered tolerance;
- calibration does not regress beyond tolerance;
- anti-forgetting regression count stays within gate.

Task improvement alone is insufficient. A faster or more accurate candidate that forgets previously frozen behavior is rejected.

The decision is serializable as a promotion manifest so later audits can distinguish "trained" from "promoted".

This still does not perform autonomous weight training. It governs whether a produced candidate is eligible to replace the frozen runtime.
