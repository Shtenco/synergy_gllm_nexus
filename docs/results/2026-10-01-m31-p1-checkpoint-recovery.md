# M31 — Frozen P1 checkpoint forensic recovery

**Date:** 2026-10-01

The committed P1 `router.pt` had the expected historical SHA-256 but was not a valid PyTorch archive. GitHub Actions reproduced:

- bytes: 4176
- SHA-256: `8c033689bacf2b70539359ecb0c2489e5154d618db0a47ec283a195f5e883947`
- `zipfile.is_zipfile`: false
- `torch.load`: FAIL — invalid/corrupted archive

A deterministic forensic reconstruction was run from the frozen P1 training provenance:

- seed 17
- train 50,000
- dev 5,000
- OOS 5,000
- epochs 14

The rebuilt `metrics.json` matched the frozen metrics **exactly**. No metric changed.

Recovered router:

- byte SHA-256: `c6c00def6ed8fb948915802e2f87e95ad9408b63020251c8a4264818c1785125`
- logical state SHA-256: `78f0f7bc6fddb26114c25f5a1370c617b382595ff6cc4ce9bd4346a1d881bd83`

The recovery audit ran in GitHub Actions run `36878807840` and uploaded artifact `11171315034`.

Integrity v2 now verifies both bytes and executable checkpoint structure: every P1 torch payload must load with `torch.load(weights_only=True)`, and recovered logical-state hashes are checked against `recovery.json`. A SHA-only manifest can no longer certify an unreadable checkpoint.

This is checkpoint-byte recovery of the frozen P1 system, not a new routing experiment and not post-B2 tuning.
