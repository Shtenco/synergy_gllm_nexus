# NEXUS-UB2/1

Frozen 2,140-case blind benchmark for Unified NEXUS v2.

The repository freezes the preregistration, schema, generator mirror, validator, scorer, seed and SHA-256 manifest. The byte-identical blind JSONL files are distributed in the immutable `NEXUS_UB2_FROZEN_2026-09-16.zip` bundle because the available chat GitHub connector writes UTF-8 through the Contents API and is not appropriate for multi-megabyte blind payloads.

Canonical frozen bundle SHA-256:
`a5bcbfb64942120f7d8469bebb3de92a9e0d19fa3701749d8a89beb8ff4872c9`

Reproducibility rule: a regenerated suite is valid only when every file SHA-256 and the suite digest exactly match `frozen/NEXUS_UB2_FREEZE_MANIFEST.json`. `source_hashes` in that manifest refer to the exact generator/validator/scorer bytes inside the canonical ZIP; the repository generator is a readable mirror.

Do not use blind content for tuning. No post-Blind tuning is permitted.
