# CRC-R1 M14 — Versioned Belief State

**Date:** 2026-09-30

CRC state had a place for `belief_ids` but no explicit epistemic ledger. M14 adds a versioned belief layer so proposed, user-asserted and verified information cannot collapse into one undifferentiated fact store.

Statuses:
- PROPOSED
- ASSERTED
- VERIFIED
- REJECTED
- CONFLICTED
- SUPERSEDED

Conflicting VERIFIED beliefs remain `CONFLICTED`; the ledger does not select a winner by confidence alone. VERIFIED may outrank a proposal for use, but the proposal remains in history. Revisions preserve parent links.

A bridge maps M12 semantic authority decisions into beliefs, keeping:
- parser proposals as PROPOSED;
- user-only context as ASSERTED;
- independently authorized facts as VERIFIED;
- rejected atoms as REJECTED.

This gives the SelfModel/Future Tree a future place to reason over uncertainty without corrupting the verified world.
