# CRC-R1 M4b.1 — Explicit Negative Semantics

**Date:** 2026-09-30

The higher-order interpreter previously inherited the legacy V3 executor's three-state gap: positive proofs returned `True`, but absence generally returned `None`; therefore explicit logical falsehood was not reachable through higher-order guards.

M4b.1 adds a narrow rule:

- proved positive → `True`
- exact explicit negative fact → `False`
- absent/unproved → `None`

No closed-world assumption is introduced.

This unlocks honest semantics for:
- `IF(false, body)` → `CONDITION_FALSE`;
- `INHIBIT(false_blocker, body)` → body executes;
- unresolved guard/blocker remains fail-closed.

HARD-OOS F v1 is **not rewritten or rescored** by this commit. Because v1 has already been generated/opened in development history, negative-gate coverage will be introduced as a new sealed HARD-OOS F2 family rather than silently mutating the old protocol.

FTX1 remains sealed and unused.
