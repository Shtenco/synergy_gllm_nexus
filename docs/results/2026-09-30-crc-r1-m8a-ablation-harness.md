# CRC-R1 M8a — Component Ablation Harness

**Date:** 2026-09-30

M8a creates one reproducible ablation report over the major CRC-R1 additions.

It does not collapse incomparable benchmark percentages into a single "intelligence score". Each component is compared only against its own relevant control:

| Component | Control | CRC treatment |
|---|---|---|
| Program representation | fixed-basis representation failure | higher-order compositional executor |
| Memory | bounded flat recency window | versioned hierarchical memory with RAW provenance |
| Future planning | depth-1 learned planning | depth-3 learned planning |
| Credit | spurious contributor trust | causal contributor trust under recursive/counterfactual credit |
| Meta-control | easy-case compute allocation | hard/novel-case adaptive allocation |

The report records deltas per component but deliberately does not average them.

## Why this matters

A monolithic score could hide regressions. M8 instead asks five falsifiable questions:
1. Did compositional execution reduce representation failure?
2. Did persistent memory preserve both answer and provenance?
3. Did extra planning depth help on delayed-reward environments?
4. Did recursive credit separate causal from spurious contributors?
5. Did metacontrol allocate more compute when novelty/uncertainty increased?

Routing is kept outside this development ablation because its next clean measurement is the sealed B2 one-shot.

## Next gate

Run this harness plus B2 and HARD-OOS F under GitHub CI from an exact commit, capture results as immutable workflow artifacts, and only then freeze the CRC-R1 pre-FTX1 candidate.
