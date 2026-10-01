# CRC-R1 M18 — Evidence-Preserving Memory Consolidation

**Date:** 2026-09-30

CRC hierarchical memory could already represent abstraction levels, but promotion between levels was manual. M18 adds the first automatic consolidator.

## Promotion rule

Repeated RAW/EPISODIC evidence may be proposed for SEMANTIC consolidation only when:
- support count meets a threshold;
- mean confidence meets a threshold;
- repeated key/value evidence is internally consistent.

Conflicting values for the same key are not compressed into a single semantic record. They remain separate evidence for the Belief Ledger to resolve.

## No destructive compression

Consolidation never deletes RAW records. Every created semantic memory stores transitive `raw_provenance`, and the standard provenance audit must remain clean.

The active working set may prefer higher-level abstractions, but any abstraction remains reversible through lineage.

This gives NEXUS a first concrete form of memory compression that reduces cognitive working-set pressure without erasing evidence.
