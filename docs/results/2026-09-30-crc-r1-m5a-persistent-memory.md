# CRC-R1 M5a — Persistent Memory + Long-History Benchmark

**Date:** 2026-09-30

M5a adds versioned persistent memory on top of the CRC hierarchical store and a long-history benchmark with revisions and distractor floods.

## Memory semantics
Every upsert writes a RAW evidence event and a SEMANTIC version. A revision does not overwrite the previous semantic record; it creates a new version that references both the new RAW evidence and the previous semantic version. Therefore the current answer can be traced through the entire revision chain.

APIs:
- `upsert(key, value, evidence)`
- `current(key)`
- `history(key)`
- `evidence(key)`
- `audit()`

## Benchmark
Each case writes a target fact, floods memory with distractors, revises the target, floods again, then queries the current value. Scoring checks both current-value accuracy and whether the answer retains at least both RAW target evidence events.

A bounded flat recency window is included only as a memory-capacity control; it is not presented as a competitive architecture.

## Scientific boundary
This benchmark validates persistence/revision/provenance mechanics. It does not yet test semantic retrieval from natural language, learned compression quality, or million-turn scale.

Next: M5b real Future Tree prediction and branch-credit benchmark.
