# CRC-R1 M9c — Local LLM/Ollama Surface Backend

**Date:** 2026-09-30

A fresh Drive audit of the historical LLM Hub found only backend/frontend source, README and launcher. No stored `models/` payload or Llama-3.3-70B GGUF was located. The README references `ollama pull llama3.3`, which is an external model acquisition instruction, not evidence that a 70B model artifact is preserved in NEXUS storage.

Therefore the architecture now distinguishes:
- **external runnable backend capability** — implemented;
- **verified model payload** — currently absent;
- **active generative cortex** — deterministic until an admitted model is present.

## Ollama adapter

`OllamaSurfaceBackend` can call a local Ollama-compatible endpoint, but requires a 64-hex verified model digest in its model reference. It receives only a `SurfaceContract` and requests low-temperature Russian lexicalization. It has no tool, memory, world-state or proof authority.

## Selection

`GenerativeBackendSelector` only mounts model IDs admitted by `GenerativeCortexRegistry`. If none are admitted, deterministic V3 rendering is mandatory.

Even an admitted model remains behind `SurfaceSemanticGuard`; an output that invents a number/entity or flips semantics falls back to deterministic rendering.

## Current status

`GENERATIVE_RUNTIME_INTERFACE = READY`  
`VERIFIED_STRONG_MODEL_PAYLOAD = NOT FOUND`  
`ACTIVE_STRONG_LLM_CORTEX = NO`

This preserves a truthful boundary while making the system ready for a real Qwen/Llama checkpoint when its bytes/digest become available.
