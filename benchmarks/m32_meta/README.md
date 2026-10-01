# M32-META

Independent development meta-protocol for M32 generalized ingress.

This is **not FTX2** and does not restore clean status to FTX1. FTX1 remains `CONSUMED_FTX1` permanently.

The META generator uses its own seed and family configuration, distinct from `M32-DEV`. Before any integrated META scoring, its generator hash, seed, case count and exact M32 implementation commit are written to an immutable `nexus.m32.meta.freeze.v1` manifest.

A sealed manifest may be re-read if byte-for-byte identical, but `write_manifest()` refuses changed generator or implementation identities.

FTX2 must be authored and sealed only after the M32 architecture and thresholds are frozen.