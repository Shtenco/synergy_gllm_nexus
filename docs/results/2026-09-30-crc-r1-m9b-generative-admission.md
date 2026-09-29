# CRC-R1 M9b — Generative Cortex Artifact Admission

**Date:** 2026-09-30

## Fresh artifact audit

Google Drive was re-checked before adding a generative backend.

### R2.1 / Qwen3 14B
Located:
- `NEXUS_R2.1_QWEN3_14B_SOURCE_ALPHA.zip` — 99,381 bytes
- `NEXUS_R2.1_QWEN3_14B_SOURCE_PHASE2.zip` — 123,599 bytes
- `qwen3-14b-r21-evidence.zip` — 2,799 bytes

The folder named `02_QWEN3_14B_MODEL` currently contains only a relay subfolder and the tiny evidence archive; no full 14B model checkpoint was found.

### R2 / Qwen2.5 0.5B
Located audit documents, but no model checkpoint payload in the audited Drive folders.

Therefore current status is:

`NO_RUNNABLE_GENERATIVE_CHECKPOINT_FOUND`

R2.1 remains source/integration evidence, not a completed 14B release.

## Admission law

A generative cortex can become active only when:
- artifact kind is CHECKPOINT, GGUF or SAFETENSORS;
- exact SHA-256 is present;
- payload is non-empty;
- model is explicitly surface-only;
- evaluation is frozen;
- semantic fidelity >= 0.99;
- guard pass >= 0.99;
- hallucination rate <= 0.01;
- regression count = 0.

Source ZIPs and evidence ZIPs are categorically non-runnable and cannot pass admission regardless of their filenames.

## Next

The architecture is now ready to mount a future real Russian cortex without confusing source code or historical claims with executable weights. The next model-search/recovery pass should target actual `.safetensors`, `.gguf`, model shards, or a reproducible external base-model identifier plus a frozen adapter/checkpoint.

FTX1 remains sealed.
