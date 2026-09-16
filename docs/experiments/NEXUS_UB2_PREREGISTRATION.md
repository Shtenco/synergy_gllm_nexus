# NEXUS-UB2/1 Preregistration

**Status:** PRE-GENERATION / PRE-IMPLEMENTATION  
**Date:** 2026-09-16  
**Blind suite size:** 2,140  
**Rule:** freeze all blind artifacts before the first Unified v2 implementation commit.

## Frozen capability specification

| Track | Blind cases |
|---|---:|
| Russian Free Dialogue | 300 |
| Long Memory 30-100 turns | 300 |
| Russian Coreference | 300 |
| Complex Causality | 300 |
| Research & Evidence | 300 |
| Graph OOD Reasoning | 320 |
| Unseen Task Induction | 320 |
| **TOTAL** | **2140** |

## Primary score

`UB2 Full = total strict semantic-contract correct / 2140`

Missing tracks count as zero for an executed candidate. A candidate with no UB2 run is `NR`, not zero.

## Promotion gates

- UB2 Full >= 70%
- all seven tracks >= 60%
- Long Memory >= 80% on deterministically resolvable cases
- Coreference >= 80% on deterministically resolvable cases
- Research & Evidence >= 80% on deterministically resolvable cases
- fabricated/invalid citation rate <= 1%
- semantic-guard factual mutation rate = 0
- no post-Blind tuning

## Anti-leakage constraints

- no split-identifying entity prefixes or lexical markers;
- generator seeds and template families are frozen before model implementation;
- blind files are hash-frozen;
- hidden blind corpus is not used for tuning;
- actual graph depth equals declared D1-D8 edge depth;
- Research & Evidence uses a frozen local evidence corpus;
- no post-Blind tuning.

## Pre-Blind requirements

Before opening UB2 blind:
1. Unified v2 source commit frozen.
2. Every organ checkpoint/adapter hash recorded.
3. Configuration digest recorded.
4. UB1 full run complete.
5. dev/shadow results complete.
6. ablation suite complete.
7. pre-Blind manifest committed.

## One-shot rule

The final blind suite is opened once. If promotion fails, the result remains part of the permanent record. Any subsequent model change requires a new frozen benchmark generation/version.