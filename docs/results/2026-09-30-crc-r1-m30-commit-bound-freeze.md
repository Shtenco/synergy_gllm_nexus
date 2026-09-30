# CRC-R1 M30 — Commit-Bound Pre-FTX1 Freeze

**Date:** 2026-09-30

A governance flaw was found after validation.v3: a green evidence manifest was content-hashed, but the freeze operation did not require the manifest's recorded commit to equal the code commit being frozen.

M30 closes this replay gap.

A pre-FTX1 freeze now requires:

```
validation schema == v3
all required gates == true
FTX1 boundary intact
HARD-OOS D boundary intact
evidence.commit == requested frozen commit
```

The produced freeze manifest records both `commit` and `evidence_commit` and they must be identical.

This prevents a green manifest from an older CRC-R1 revision being replayed to bless newer, unvalidated code.

A portable `scripts/crc_r1_freeze.py` entrypoint is added. It does not open or evaluate FTX1.
