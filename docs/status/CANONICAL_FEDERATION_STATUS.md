# NEXUS federation — canonical status

**Date:** 2026-09-30  
**Branch:** `crc-r1-foundation`

```text
operational_verified      11 / 11  READY
historical_byte_identical 10 / 11
```

## Operational federation

All eleven required operational slots are available.

- R7-L — exact runnable
- R7.2 — exact runnable
- R7.6 — exact runnable
- R7.8 — exact runnable
- R7.10 — exact runnable
- R7.14 — exact runnable
- R7.18 — exact runnable
- R7.44.3 — **EXACT_DEPLOYED_RUNTIME**
- Ω-1.5R2 — exact runnable
- V10 600K — exact runnable
- authority slot — **R1.3-X V2/V3 VERIFIED_OPERATIONAL_RUNTIME**

Therefore federation recovery does **not** block further CRC-R1 development.

## Historical identity boundary

The byte-identical historical ledger is 10/11 because the original Unified R1.3 release tree has not been recovered.

This is an identity/provenance gap, not an operational federation gap.

R1.3-X must never be renamed to the original historical Unified R1.3.

## R7.44.3 recovery

The deployed MOBILE PORT was recovered byte-for-byte from `SINERGIYA-FINANS-v8.0.1-NEXUS-R7443-MAX.apk`.

SHA-256:

`d248bb75c45694bbde6914615243080b711d2efea80b22c2652e692cc8307703`

Targeted contract replay: **8/8**.

## R1.3-X operational authority

- PR #6: R1.3-X V2 exact cognitive Russian runtime
- head: `4735ca4f36d441f4fa2de6af4c704d5140a6c586`
- PR #7: R1.3-X V3 compositional authority governor
- head: `105a692d64a42d6c772de69dcaeb16ac27833b01`
- frozen authority benchmark: **12/12**
- Drive archival slot: `05_R1_3_X_VERIFIED_RUNTIME`

## Canonical rule

Do not report `9/11 + two blockers`.

Report:

```text
M0 operational federation     ✅ 11 / 11 READY
R7.44.3                       ✅ EXACT_DEPLOYED_RUNTIME
R1.3-X V2/V3                  ✅ VERIFIED_OPERATIONAL_RUNTIME
Original historical R1.3     ⚠ only historical identity gap
```
