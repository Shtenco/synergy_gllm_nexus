# M0 correction — recovered federation ledger

**Date:** 2026-09-30

The earlier CRC-R1 M0 report incorrectly regressed to **9/11 + two blockers** because the branch was created from a base that did not contain the later recovery work from PR #4, PR #6 and PR #7.

## Correct status

### Historical byte-identical recovery

**10/11**

Recovered and accepted:
R7-L, R7.2, R7.6, R7.8, R7.10, R7.14, R7.18, **R7.44.3 exact deployed MOBILE PORT**, Ω-1.5R2, V10.

The only historical-byte blocker is the original Unified R1.3 release tree.

R7.44.3 is not a blocker. PR #4 recovered the byte-identical deployed runtime from `SINERGIYA-FINANS-v8.0.1-NEXUS-R7443-MAX.apk` with SHA-256:

`d248bb75c45694bbde6914615243080b711d2efea80b22c2652e692cc8307703`

Targeted replay: **8/8**.

### Operational verified federation

**11/11 READY**

The authority slot is satisfied by **R1.3-X V3**, while preserving the historical identity distinction.

Evidence:
- PR #6: `NEXUS R1.3-X V2: exact cognitive Russian runtime`, head `4735ca4f36d441f4fa2de6af4c704d5140a6c586`;
- PR #7: `NEXUS R1.3-X V3: compositional authority governor`, head `105a692d64a42d6c772de69dcaeb16ac27833b01`;
- V2 mounted exact R7.6/R7.8/R7.10/R7.14 organs with frozen hashes;
- V3 fresh AUTHORITY-CONFLICT-V3-B2: **12/12 = 100%**;
- Google Drive has the dedicated archive slot `05_R1_3_X_VERIFIED_RUNTIME` (folder ID `1tFfxfIxNon9RdxFTPg7Hq0b67l4bKOaO`).

R1.3-X is an operational verified successor/runtime and is **not** relabelled as the byte-identical historical Unified R1.3 release.

## Canonical rule from this commit

Never report `9/11 + R7.44.3 blocker` again.

Use:
- `historical_byte_identical = 10/11`
- `operational_verified = 11/11 READY`
