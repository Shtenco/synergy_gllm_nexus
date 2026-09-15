# NEXUS — Cross-generation benchmark and audit comparison

**Date:** 2026-09-16

## Methodological rule

This document does **not** rank raw percentages from different frozen/sealed protocols as one leaderboard. A 95% score on a context-state benchmark is not numerically comparable to 5.41% exact joint-triple construction on a harder cross-generation graph benchmark. Each result is preserved in its native protocol, with evidence grade and scope.

## Selected evidence-backed generations

| Version | Native evidence | Evidence grade | What it demonstrates | Main limitation |
|---|---|---|---|---|
| Unified R1.3 | 164/188 = 87.23%; open-set 30/30; 117/117 frozen files unchanged | A historical sealed | Best overall reproducible NEXUS compound release; still not an open-domain frontier LLM or AGI. | best broad compound behavior in line |
| R7.2 Ω Disentangled Natural | Blind-20: 100%, 16 ops / 320 episodes; parser 98.125% | A blind | Best structured Russian binder in Ω line; not free-form generative chat. | strong structured Russian; not arbitrary prose |
| R7.9 Ω Formal Semantic Dual Node | Blind-26: single 112/120=93.33%; dual 114/120=95.00% | A-/B+ | Strong proof-first reasoning; dual gain not statistically established and source reconstruction caveat exists. | not free chat |
| R7.12 Ω GraphBoost | Blind-28: 133/160=83.125%; baseline 130/160; verified proof soundness 29/31 | A- blind | Positive but non-significant +3 corrections; exposed proof-certification bottleneck. | not free chat |
| R7.14 Ω MorphoLex | 150/150 deterministic tests; CV consistency 96.45%; direct downstream 93.75% -> 93.43% (worse) | A- component | Useful language parser; direct answer authority correctly disabled after regression. | Russian parsing/canonicalization only |
| R7.17 Ω Adaptive Recurrent Reasoning | Blind-30: 129/200=64.5%; 0 corrections / 0 regressions vs R7.16 | A blind | No measured accuracy gain over R7.16 on fresh Blind-30. | not chat |
| R7.18 Ω Best-of Evidence Credit | Blind-31: 156/200=78.0%; R7.16/R7.17 70%; best single teacher 71.5%; oracle 90.5% | A blind | Best later structured reasoning/governor evidence; strong evidence/policy, multilingual, probability; weak algebra 28%. | not free chat |
| R7.44.3 Ω | Blind-65: 2400/2400 context; Dialogue-65 25/25 context checks across 30 Russian turns | A context | Closest existing Russian discourse shell, but explicitly not unrestricted language understanding or free generator. | best tested multi-turn context layer |
| R7.45.2 Ω Business Executive | final new post-freeze 20Q: 15/20=75%; disclosed replays 19/20 + 19/20 | A- post-freeze domain | Best business specialist found; not a universal conversational cortex. | business dialogue only |
| SINERGIYA-FINANS NEXUS V8.0 Recurrent Latent | official: conversation E2E 16/16, latent narrow holdout 100/100%; fresh audit: 16/16 after path shim; 11/12 general prompts visibly off-domain/misrouted | A- domain / fresh runtime | Strong local finance assistant, not a general Russian conversational model; packaging test path mismatch also found. | good scripted finance multi-turn; fails open-domain conversation |
| V10 600K InfoGraph | ARC seen pass@2 88.83%; unseen hash-split pass@2 84.83% | A- procedural | Strong procedural ARC baseline; not general language intelligence. | 0/25 (not implemented) |
| V30 | dialogue 0/25; ARC unseen pass@2 85.92%; neural unseen sequence accuracy 0.25% | A | Excellent warning example: high synthetic logic/ARC metrics coexist with total natural-language failure. | 0/25; pseudo-words/repetition |
| Ω-1.2 Graph Compiler Smoke | Blind-1 relation accuracy 40.0%; strict graph 0.0% | A current local smoke | Useful baseline only; tiny CPU smoke model, not a competitive graph constructor. | not dialogue; structured relation compiler |
| Ω-1.3 Graph Construction Cortex | Blind-1 relation 38.61%; subject 35.75%; object 78.95%; strict non-abstain graph 0.60% | A- current held-out with prior format/surface inspection caveat | First non-zero exact graph construction, but relation generalization failed its >40% gate. | structured Russian relation extraction |
| Ω-1.4 Semantic Operator Cortex | Blind-2A relation 76.60%; Blind-2B relation 50.00%; strict non-abstain graph remained 0%; NOTA precision below gate | A- current internal frozen suite; two first rows viewed after freeze before evaluation | Large relation-semantic gain; argument construction and open-set calibration became the bottlenecks. | relation semantics, not free dialogue |
| Ω-1.5 Universal Graph Argument Cortex | Blind-3A relation 86.20%, joint triple 5.41%, candidate-both recall 97.22%; Blind-3B relation 75.10%, joint triple 1.63%, candidate-both recall 95.80% | A current internal frozen suite | First non-zero joint triple exact on new Blind-3 where Ω-1.4 was 0%; promotion still blocked by candidate recall<99 on blind and NOTA precision. | structured Russian triple construction, not free dialogue |

## Capability-wise comparison

### Structured Russian language / binding
- **R7.2** remains the strongest historical structured Russian binder in its own Blind-20 protocol: 100% over 16 held-out operators / 320 episodes, parser 98.125%. This is stronger than new Ω on that specific binder task, but it is not arbitrary prose or exact triple construction.
- **R7.14 MorphoLex** is a useful multilingual parsing/canonicalization organ (150/150 deterministic tests; 96.45% CV consistency), but direct answer authority slightly worsened downstream accuracy, so disabling its sovereignty was correct.

### Structured reasoning / evidence governor
- **R7.9** reported 93.33% single and 95.00% dual on Blind-26; the dual improvement was not statistically established.
- **R7.12** GraphBoost improved Blind-28 from 130/160 to 133/160 (83.125%), a small positive but non-significant gain.
- **R7.17** produced no fresh Blind-30 gain over R7.16 (both 129/200 = 64.5%).
- **R7.18** is the strongest later historical reasoning/evidence-governor result found: Blind-31 156/200 = 78%, versus 70% for R7.16/17 and 71.5% best single teacher. It remains a structured reasoning benchmark, not general language.

### Context / dialogue state
- **R7.44.3** is the strongest historical context shell located: Blind-65 2400/2400 context plus Dialogue-65 25/25 context checks across 30 Russian turns. Its scope is discourse/context state, not free generation.
- **SINERGIYA-FINANS V8.0** reproduces 16/16 scripted finance conversation after a packaging shim, but 11/12 fresh general prompts were visibly off-domain or misrouted; it is a finance assistant, not a general conversational model.

### Procedural / ARC specialist capability
- **V10 600K InfoGraph**: ARC seen pass@2 88.83%, unseen hash-split pass@2 84.83%. Strong specialist result; no chat runtime.
- **V30**: ARC unseen pass@2 85.92% while dialogue was 0/25 and unseen neural sequence accuracy 0.25%. This is the clearest historical warning against inferring general intelligence from synthetic/procedural scores.

### New Ω graph-language line
- **Ω-1.2**: 40% relation, 0% strict graph — baseline smoke only.
- **Ω-1.3**: first non-zero strict graph construction (0.60% strict non-abstain), but relation 38.61% failed its gate.
- **Ω-1.4**: relation semantics improved sharply on Blind-2A/B (76.6% / 50.0%), but exact graph stayed at 0 because argument extraction failed.
- **Ω-1.5**: on new Blind-3A, relation 86.20% and joint exact 5.41%; on Blind-3B, relation 75.10% and joint exact 1.63%. On the same Blind-3 corpora, Ω-1.4 joint exact was 0% on both. This is the strongest direct evidence so far for cross-surface exact triple construction in the new Ω line, but it is still far from solved.

## Neutral conclusion

- There is **no single historical NEXUS that dominates all capability classes**.
- Historical R7.x systems often outperform Ω-1.5 on their own narrower structured reasoning/context benchmarks.
- Ω-1.5 provides a qualitatively new capability not demonstrated by those percentages: non-zero exact `(SUBJECT, OPERATOR, OBJECT)` construction on a separately frozen cross-generation Russian Blind-3 where Ω-1.4 scored zero joint exact.
- The strongest engineering direction is therefore compositional: preserve R7.18 evidence governance, R7.44.3 context, R7.2/R7.14 language constraints, Ω-1.4 semantic operators and Ω-1.5 joint graph construction, then add Ω-1.6 external evidence acquisition without giving web tools authority.

## Evidence limitations

- Many historical artifacts are internal frozen/sealed benchmarks rather than public standardized benchmarks.
- Some versions have physical releases; others are referenced-only or historical reports. Evidence grades in the ledger preserve that distinction.
- New Ω Blind suites are internal and synthetic/hybrid. They demonstrate engineering progress inside this research program, not unrestricted Russian understanding or AGI.