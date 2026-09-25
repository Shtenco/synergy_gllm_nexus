# ORIGINALS — immutable recovery vault

This directory is reserved for exact historical bytes.

Rules:
1. Never edit an original in place.
2. Copy the byte-for-byte artifact first.
3. Record SHA-256, source path/archive, acquisition date and provenance.
4. Put all upgrades under recovery/r13x/ or another explicitly versioned path.
5. A historical claim without the bytes is marked historical_lead, never recovered.

Current state (2026-09-26): the exact V4.2 checkpoint payload and exact historical Unified R1.3 release are not verified as mounted bytes. Their known hashes/leads are retained only in RECOVERY_INDEX.json.
