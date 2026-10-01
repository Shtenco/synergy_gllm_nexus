# CRC-R1 PRE-FTX1 Freeze Attestation

**Validated commit:** `fded8bd46777b2e868620b4c85d60c5c375b5ec1`

**Validation workflow:** `crc-r1-validation` run `36884741351` (#60) — **SUCCESS**

**Validation evidence artifact:** `crc-r1-validation-v3-evidence`, artifact id `11173742450`

**Artifact digest:** `sha256:dcea444fe56d564cf62ff2ccacb84df28b0e214494eafb3b3931da1887e1c836`

**Evidence manifest SHA-256:** `ef1626b44215c149c8dacf4ddc2fa83709c050f7bf76f5711f6df43a6caa197d`

**Freeze manifest SHA-256:** `fc14ffc4c5b028a64d9dcddd1afeb456609519b4f093c3e541df233a364ded27`

## Gate result

`PreFTX1FreezeGate` semantics were applied to the exact validation.v3 evidence manifest. All 22 required gates are `true`; `ready_for_pre_ftx1_freeze=true`; `ftx1_used=false`; `hard_oos_d_reused_as_clean_oos=false`; and `evidence.commit` exactly equals the validated commit.

Result: **`FROZEN_PRE_FTX1`**.

## Identity boundary

This attestation branch is a child of the validated commit and contains only freeze/evidence records. Its attestation commit is **not** presented as a newly validated runtime. The frozen runtime identity remains exactly `fded8bd46777b2e868620b4c85d60c5c375b5ec1`.

FTX1 remains sealed and unopened by this attestation.
