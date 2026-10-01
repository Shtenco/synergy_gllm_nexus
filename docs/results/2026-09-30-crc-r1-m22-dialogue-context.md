# CRC-R1 M22 — Dialogue Context R1

**Date:** 2026-09-30

M22 adds a new CRC dialogue-state organ. It is explicitly **not** relabelled as the missing exact R7.44.3 runtime.

## State

The context manager tracks:
- session and hard-boundary IDs;
- turn number;
- versioned context values;
- pending slots;
- local referents;
- append-only context trace.

## Rules

- latest compatible referent resolves inside the current boundary;
- hard context boundaries clear transient referents/pending slots while preserving explicit long-lived values/history;
- pending slots are typed and filled explicitly;
- VERIFIED context values outrank ASSERTED values;
- a later assertion cannot silently overwrite an active VERIFIED value;
- a later VERIFIED value may supersede an older VERIFIED value, but the old version remains in history.

This reproduces the *architectural role* needed by CRC without claiming recovery of R7.44.3's missing transitive dependencies.

Next integration: M23 will join language proposal, semantic authority, belief/context state and guarded surface generation into one conversation shell.
