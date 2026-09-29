# CRC-R1 M1.1 — Frozen P1 feature-contract hardening

Before opening B2 scorer-only gold, production feature tensorization is made explicit.

P1 was trained on eight continuous features. Runtime semantic extraction still exposes categorical fields such as `language` and `evidence_conflict`, but `RouterFeatures` now also accepts optional continuous `ru_signal` and `evidence_signal`. The frozen P1 tensorizer uses those exact continuous values when supplied and falls back to the semantic booleans otherwise.

This prevents B2 from accidentally measuring an undocumented continuous→binary quantization layer in addition to router generalization.
