# NEXUS Unified v2 + NEXUS-UB2 Design Specification

**Status:** APPROVED ARCHITECTURE / PRE-IMPLEMENTATION  
**Date:** 2026-09-16  
**Repository:** `Shtenco/synergy_gllm_nexus`  
**Base lineage:** `omega15r2-blind4-v1` @ `f70a3c316775c763a94fbc55a8fae84c326ab60e`  
**Design branch:** `unified-nexus-v2-ub2-design`  
**Scientific rule:** UB2 must be frozen before the first implementation line of Unified v2.

## 1. Goal

Build the first NEXUS release that combines the strongest reproducible organs from the R-line, GLLM Ω-line and Unified Rebuild line into one sovereign modular runtime, while preserving provenance and preventing any surface-language generator from changing the underlying facts.

Promotion requires both `UB1 Full Strict >= 80%` on frozen NEXUS-UB1 and `UB2 Full >= 70%` on frozen NEXUS-UB2. Historical Blind/ARC/dialogue scores are side evidence only.

## 2. Selected architecture

The design rejects physical weight mixing and a learned MoE router as the primary v2 integration mechanism. The selected architecture is a **typed sovereign organ bus**: each organ has a typed contract, can be ablated independently, emits proposals rather than uncontrolled truth, and preserves donor/checkpoint provenance.

## 3. Twelve organs

| # | Organ | Donor | Function |
|---|---|---|---|
| 1 | Unified Graph Workspace | Unified Rebuild v1 | canonical state for entities, claims, graph edges, evidence and revisions |
| 2 | Native Formal Authority | R7.8 | deterministic/formal authority; fresh UB1 formal 95% |
| 3 | Russian Binder | R7.2 | Russian text -> structured semantic state; UB1 operator transfer 160/160 |
| 4 | Morpholex Cortex | R7.14 | morphology, normalization, canonicalization, Russian logical operators |
| 5 | Semantic Operator Cortex | Ω-1.4R | relation/operator classification |
| 6 | Universal Role Binder | Ω-1.5R2 | SUBJECT/OBJECT assignment; UB1 relation-binding strict 71.43% |
| 7 | Unseen Operator Cortex | R7-L | structural unseen-operator reasoning; UB1 160/160 |
| 8 | Recurrent Reasoning Cortex | R7.17 | hypothesis/revision/recurrent reasoning |
| 9 | Evidence Governor | R7.18 + R7.10 | proof-first authority, evidence credit, contradiction handling, abstention |
| 10 | Context Cortex v2 | rebuilt context + R7.44.3 contracts | anaphora, pending slots, suspend/resume, topic boundaries and revision |
| 11 | Research Cortex | Ω-1.6 | query planning, evidence federation, provenance and citation ledger |
| 12 | Native Russian Surface Decoder v2 | new | AnswerGraph -> natural Russian; never owns factual authority |

V13/V13.3 world-model components and V17 non-local fusion are deferred Phase-2 donors so the v2.0 causal study remains attributable.

## 4. Sovereign authority model

The bus operates on immutable typed envelopes such as `TextTurn`, `EntityRef`, `Claim`, `EvidenceItem`, and `AnswerGraph`.

Rules:
- Binder, morphology, relation, role, context and research organs emit proposals.
- Graph Workspace stores candidate and committed state separately.
- Evidence Governor promotes candidate claims after validation.
- Formal Authority directly commits only derivations inside its supported formal domain.
- Research Cortex provides evidence proposals and has no mutation authority over external systems.
- Surface Decoder receives a frozen AnswerGraph and cannot create/remove/alter claims.
- Semantic Consistency Guard rejects generated Russian text that adds entities, numbers, polarity, causal edges, citations or certainty not licensed by the AnswerGraph.

## 5. Request pipeline

```text
Russian user text
  -> Morpholex Cortex
  -> Russian Binder
  -> Semantic Operator Cortex
  -> Universal Role Binder
  -> Context Cortex v2
  -> Unified Graph Workspace
  -> Native Formal Authority / Unseen Operator Cortex
  -> Recurrent Reasoning Cortex
  -> Evidence Governor
  -> Research Cortex when evidence acquisition is justified
  -> Evidence Governor re-validation
  -> AnswerGraph
  -> Native Russian Surface Decoder v2
  -> Semantic Consistency Guard
  -> Russian response
```

Routing is capability-based. Every bypass is recorded in the execution trace.

## 6. Context Cortex v2

R7.44.3 is **not** claimed to be restored because its exact R7.38 dependency remains missing/conflicted. v2 reimplements documented contracts: `AnaphoraBinder`, `PendingSlotFrame`, `HardContextBoundary`, suspend/resume, stale-fact invalidation after user correction, topic-scoped memory and provenance for remembered facts. An exact restored R7.44.3 can later be placed behind the same interface.

## 7. Native Russian Surface Decoder v2

The decoder optimizes Russian naturalness under a hard semantic constraint. It must preserve numbers, named entities, negation, causal direction, certainty/uncertainty and citations. It may ask a clarification only when the AnswerGraph marks an unresolved required slot. Naturalness never overrides semantic faithfulness.

## 8. NEXUS-UB2/1

| Track | Blind cases | Purpose |
|---|---:|---|
| Russian Free Dialogue | 300 | natural response, follow-up, clarification, user corrections |
| Long Memory 30-100 turns | 300 | 30/50/75/100-turn persistence, revisions, stale facts |
| Russian Coreference | 300 | pronouns, demonstratives, ambiguous references, entity continuity |
| Complex Causality | 300 | causal chains, blockers, counterfactuals, competing causes |
| Research & Evidence | 300 | conflicting sources, provenance, citations, abstention |
| Graph OOD Reasoning | 320 | D1-D8 temporal/causal/is-a/mixed graphs |
| Unseen Task Induction | 320 | new rules/operators/microworlds |
| **TOTAL** | **2140** | |

Free Dialogue uses semantic contracts: required claims, forbidden claims, correction behavior, clarification conditions and uncertainty policy. Linguistic naturalness is scored separately and cannot compensate for semantic failure.

Long Memory balances 30/50/75/100 turns and includes distractor topics, revisited entities, explicit corrections, stale facts and suspended goals.

Coreference includes pronouns, demonstratives, nominal anaphora, previous-object/event references, multiple plausible antecedents and genuine clarification/abstention cases.

Complex Causality includes multi-hop causes, necessary/sufficient conditions, blockers, counterfactuals, competing explanations and temporal-vs-causal ordering.

Research & Evidence uses a **frozen local evidence corpus** for reproducibility. A future live-research benchmark is separate from UB2/1.

Graph OOD D1-D8 labels must equal actual edge depth; the UB1 off-by-one issue must not recur.

Unseen Task Induction forbids split-identifying markers and includes novel operator names/entity lexicons, reversed order, passive voice, distractors, NOTA/open-set and multi-sentence rules.

## 9. UB2 anti-leakage protocol

1. Review this design.
2. Implement UB2 generator/validator/scorer only.
3. Generate all 2,140 blind cases with fixed seeds.
4. Run structural validators.
5. Write per-split SHA-256 and top-level freeze manifest.
6. Commit complete UB2 artifacts.
7. Record the freeze commit SHA.
8. Only after that commit may the first Unified v2 implementation commit be created.
9. Blind content is not inspected during tuning.
10. No post-Blind tuning; any next attempt requires a newly named frozen protocol.

UB2 has dev, shadow and blind visibility levels. The 2,140 count is the blind promotion suite only. No lexical prefix, entity namespace, filename pattern or metadata may reveal the split.

## 10. UB1 promotion gates

Unified v2 must achieve on frozen UB1:
- UB1 Full Strict >= 80%
- Formal >= 90%
- Semantic >= 70%
- Operator Transfer >= 95%
- Relation Binding strict >= 70%
- Graph OOD >= 98%
- Context/Revision >= 98%
- Evidence/Trust >= 98%

All seven tracks must execute; a missing adapter makes promotion impossible.

## 11. UB2 promotion gates

- UB2 Full >= 70%
- every capability track >= 60%
- Long Memory >= 80% on deterministically resolvable cases
- Russian Coreference >= 80% on deterministically resolvable cases
- Research & Evidence >= 80% on deterministically resolvable cases
- invalid/fabricated citation rate <= 1%
- semantic-guard factual mutation rate = 0 on blind
- no post-Blind tuning

## 12. Regression and ablation requirements

Every organ supports an ablation flag. Required comparisons: Unified v1 baseline, full v2, v2 minus each organ, deterministic surface renderer instead of decoder, Research Cortex disabled, and Context Cortex reset each turn.

## 13. Provenance

Every run records repository commit, model/checkpoint SHA-256 per organ, donor/version, adapter SHA-256, benchmark manifest SHA-256, configuration digest, random seed and per-track raw result hashes. Unresolved historical artifacts are marked `REBUILT`, `ADAPTER` or `BLOCKED`, never `EXACT`.

## 14. Failure policy

Fail closed for authority-sensitive behavior: unsupported formal claim -> abstain/evidence; materially ambiguous coreference -> clarification; insufficient evidence -> uncertainty/abstention; decoder/AnswerGraph mismatch -> reject text; missing/corrupt checkpoint -> organ unavailable with no silent substitution.

## 15. Repository layout target

```text
benchmarks/ub2/{generator,validators,scoring,frozen}
src/nexus_gllm/unified_v2/{bus.py,contracts.py,workspace.py,runtime.py,provenance.py,guard.py}
src/nexus_gllm/unified_v2/organs/
tests/{unified_v2,ub2}/
docs/{experiments,results,superpowers/specs,superpowers/plans}/
```

## 16. Implementation order after UB2 freeze

1. UB2 generator, validators, scoring contracts and freeze.
2. Typed bus/contracts/workspace/provenance.
3. Deterministic donor adapters for exact runnable organs.
4. Context Cortex v2.
5. Semantic/role integration.
6. Reasoning + Evidence Governor orchestration.
7. Research Cortex adapter.
8. AnswerGraph + Surface Decoder + semantic guard.
9. Full UB1 execution.
10. dev/shadow regression and ablation.
11. Pre-Blind runtime/checkpoint freeze.
12. One-shot UB2 blind opening and promotion decision.

## 17. Non-goals

No physical weight merge; no learned MoE primary controller; no V13/V17 integration before v2.0 causal baseline; no claim of exact R7.44.3 restoration; no open-domain AGI claim from internal benchmarks; no live-web-dependent UB2 headline score.

## 18. Success definition

Unified v2 must be reproducible, provenance-complete, natural in Russian without factual mutation, materially stronger than Unified v1 on common UB1, robust on long dialogue/coreference/causality/evidence/unseen tasks under frozen UB2, and scientifically auditable including failed gates.