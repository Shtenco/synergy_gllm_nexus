# NEXUS GLLM Ω-1.2 — Stage A 100K Run

**Date:** 2026-09-15  
**Seed:** 17  
**Status:** experimental R&D run; PR remains draft

## Corpus

Stage A was materialized with:

- train: **100,000** situations;
- dev: **10,000** situations;
- blind: **10,000** situations;
- 10 approved task families;
- split-disjoint entity namespaces;
- split-disjoint source namespaces;
- split-disjoint **actual Russian surface templates**, not only metadata IDs.

Final belief-corpus raw SHA-256:

`103cd7ca6ca5a5808d89a3d4e01258e0d090e7b66d2ca199e447661371bf4dc7`

Compressed artifact SHA-256:

`30655b084a34f048d8f489703a7f40d6bba50e8055e6b12001547d6ffd5a4075`

## Belief-reference gate

The belief-revision thresholds were selected on dev only:

- `active_threshold = 0.70`
- `contradiction resolve_margin = 0.10`

With those values frozen, the synthetic structured scenario evaluator produced:

- dev scenario-status accuracy: **100%**;
- blind scenario-status accuracy: **100%**.

This is a deliberately synthetic belief-reference gate. It is **not** a claim of unrestricted Russian understanding, LLM-level language quality, or external SOTA.

## Derived neural compiler corpus

One Russian→Graph target was derived from every Stage-A situation:

- train: 100,000;
- dev: 10,000;
- blind: 10,000.

Raw compiler-corpus SHA-256:

`d3ea1b9afb01f371cba9b18ccd2296885a9c382730e0791984b42d8afda09d45`

## Native neural compiler smoke

A small CPU-only character BiGRU challenger was trained from scratch on the **full 100,000 train examples** for one epoch:

- embedding dim: 8;
- hidden dim: 16 per direction;
- no pretrained tokenizer;
- no pretrained LLM;
- dev relation accuracy: **40%**;
- blind relation accuracy: **40%**;
- dev strict structure accuracy: **0%**;
- blind strict structure accuracy: **0%**;
- elapsed wall time in the available CPU runner: about **19.6 s**.

Checkpoint SHA-256:

`881a9aeae6e937b4267b12c1b8e7391fa23f0d7824c7ce41a87ee0681b833806`

Interpretation: the full 100K training path is operational, but this deliberately tiny smoke configuration is under-capacity. It is not a promotion candidate.

Larger CPU-only H=32 and H=64 attempts exceeded the available execution window and produced no accepted checkpoint. They are not counted as completed training runs.

## Current gate decision

- belief/reference engine: **passes current synthetic Stage-A gate**;
- tiny neural compiler: **does not pass promotion gate**;
- scale-up to 250K is **not yet authorized**;
- next action is a proper compiler/core training run on a longer CPU runner or CUDA runner, followed by frozen blind evaluation and protected regression checks.

## CI limitation

GitHub Actions continues to terminate before useful step logs are exposed through the connected API. This is why PR #1 remains draft and this document does not claim repository-wide green CI.
