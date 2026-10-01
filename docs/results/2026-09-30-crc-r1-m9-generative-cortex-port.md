# CRC-R1 M9 — Authority-Safe Generative Cortex Port

**Date:** 2026-09-30

A strong generative cortex remains mandatory for natural Russian dialogue, but it must not become a second factual authority. M9 introduces the interface that allows a future Qwen/LLM backend to lexicalize an already-authorized semantic answer without committing facts, changing polarity or writing its prose back into reasoning state.

## Contract

The generator receives only an authority-owned `SurfaceContract`:
- epistemic state;
- authorized answer values;
- licensed entity names and numbers;
- provenance IDs;
- uncertainty;
- whether negation is semantically licensed.

Generated text is always marked `authoritative=False`.

## Guard

The first conservative guard rejects:
- unlicensed numbers;
- polarity/negation flips on a proved positive answer;
- new title-cased named entities not present in the contract.

A rejected generation is replaced with deterministic Russian realization. The generated text is never allowed to mutate Semantic IR, world facts, proof state, provenance or persistent memory.

## Why this layer is separate

The historical NEXUS audit showed that strong executive/reasoning organs can coexist with poor natural conversation. The solution is not to give a fluent LLM sovereign reasoning authority. The safer architecture is:

`verified semantics → generative surface cortex → semantic guard → user text`

while the reverse direction remains:

`user text → parser/binder → Semantic IR`

with raw text quarantined from reasoning contracts.

## Next

M9b should add a checkpointed backend-admission contract so a real Russian generative model can be mounted by SHA, measured for fidelity/fluency, and promoted behind the same surface-only interface without changing reasoning authority.

FTX1 remains sealed.
