# CRC POST-PLANNING-FIX COMMIT-BOUND FREEZE

## Frozen cognitive architecture authority

The cognitive architecture for the next blind/unseen transfer cycle is frozen at:

`97a9c7ed12900969c68ba596e629c70adb398f06`

This SHA is the architecture authority. The present document is only the post-CI freeze record and must not be interpreted as a later architecture revision.

## Why this is a new freeze

The previous frozen architecture (`6067746d3dbab7a5a0a7388545b73116fd23c25a`) produced a preserved FAR-OOS result of 85.71428571% with the mechanical verdict `PARTIAL_TRANSFER`. Six held-out families transferred at 100%, while `LONG_HORIZON_PLAN` failed at 0%.

The observed failure was traced to a concrete resource-control defect:

`MetaController depth=2 -> planner truncation -> delayed reward at step 3 invisible -> local cash_now chosen over invest`.

The post-FAR-OOS DEV regression first failed on GitHub Actions run `37138121717` with the exact behavioral mismatch `cash_now != invest`. A minimal architecture correction was then committed at the authority SHA above. The same regression passed on run `37138204374`.

The historical FAR-OOS verdict remains immutable. It is not recalculated and cannot be promoted retroactively.

## Required pre-freeze CI evidence

All PR workflows associated with architecture SHA `97a9c7ed12900969c68ba596e629c70adb398f06` completed successfully:

- `ci` run `37138204382`: SUCCESS; full `pytest -q` and `compileall` succeeded.
- `crc-equal-budget` run `37138204371`: SUCCESS; controlled DEV A->B->C->D->E contract preserved.
- `crc-post-far-oos-dev` run `37138204374`: SUCCESS; planning regression GREEN.
- `m32-ci` run `37138204351`: SUCCESS.
- `m32-evidence` run `37138204357`: SUCCESS.
- `m32-ci-windows` run `37138204354`: SUCCESS.
- `m32-evidence-windows` run `37138204412`: SUCCESS.

## Freeze contract

From this freeze record until the second blind/unseen transfer verdict is emitted:

1. No file under `src/nexus_gllm/unified_v3/cognitive/` may change relative to architecture SHA `97a9c7ed12900969c68ba596e629c70adb398f06`.
2. The next evaluator must verify that invariant before execution.
3. The previous 672 FAR-OOS scored cases and their generator must not be reused as transfer evidence.
4. The next corpus must be authored only after this freeze record, with fresh seeded instances, fresh graph structures, fresh reward layouts and planning horizons spanning 2-5.
5. Case generation must actually depend on the seed; changing the seed must change task parameters while A/B comparisons, where used, remain paired within a seed.
6. Labels/oracles must be computed independently of NEXUS decisions.
7. No architecture tuning is allowed after seeing the second blind results. Any failure starts a later DEV cycle and cannot rewrite the blind verdict.
8. `M32-META` remains SEALED / UNOPENED.
9. `FTX2` remains UNAUTHORED. This blind battery is not FTX2.
10. No new architecture/version label is introduced by this freeze.

## Scientific boundary

A successful second blind battery would support stronger out-of-development transfer evidence for the frozen cognitive mechanisms. It would still not by itself establish universal intelligence or unrestricted real-world competence.
