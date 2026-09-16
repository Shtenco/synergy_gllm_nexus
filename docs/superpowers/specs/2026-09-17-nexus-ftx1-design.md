# NEXUS-FTX1 Far-Transfer Benchmark Design

**Status:** APPROVED / PRE-IMPLEMENTATION  
**Date:** 2026-09-17  
**Branch:** `nexus-ftx1-freeze-v1`  
**Base:** NEXUS Unified v2 RC1 @ `2b47c17f4f928430da9abb83f51ccd02d871981d`

## Goal

Build a falsification-first benchmark that measures genuine far transfer rather than recognition of benchmark templates. FTX1 is the scientific gate that must be frozen before any `Unified v3 Generalization-First` implementation begins.

## Design philosophy: cybernetics + Soviet logic

These labels are operationalized, not decorative.

### Cybernetic principles

Each task is modeled as a controlled system with some subset of:
- observable state;
- hidden state;
- target/goal state;
- control action;
- disturbance;
- feedback signal;
- invariant;
- stability condition;
- controllability/observability limit;
- adaptation after error.

The benchmark rewards models that reconstruct the governing system and act on the induced rules, not models that memorize surface phrases.

### Logic principles

The benchmark uses explicit logical discipline:
- predicate and relational structure;
- implication, biconditional, negation and quantification;
- necessary vs sufficient conditions;
- proof obligations;
- contradiction ledgers;
- competing hypotheses;
- epistemic states `PROVED / DISPROVED / UNRESOLVED / CONFLICTED`;
- synthesis only when a rule or evidence path justifies it;
- no conversion of contradiction into certainty without a valid derivation.

Dialectical opposition is represented as competing claims and constraints, not as an ideological rule that contradiction is automatically resolved.

## Blind suite

FTX1 blind contains exactly **2,400 cases**, eight tracks x 300.

| Track | Cases | Primary capability |
|---|---:|---|
| semantic_rule_induction | 300 | infer previously unseen relations/operators from demonstrations |
| surface_far_transfer | 300 | preserve semantics under unseen Russian renderers and syntax |
| role_voice_coreference | 300 | roles, passive/active, inversion, pronouns, ellipsis |
| task_schema_induction | 300 | infer what operation/output schema is requested from instructions/examples |
| compositional_reasoning | 300 | compose 2-5 previously unseen operators/rules |
| cross_language_transfer | 300 | RU↔EN plus bounded RU↔KZ transfer |
| long_horizon_transfer | 300 | 30-100 turn memory in unseen ontology with revisions/disturbances |
| evidence_counterfactual | 300 | conflicting evidence, causality, counterfactuals, NOTA, abstention |

## Physical separation

FTX1 has three independent distribution families:

- `DEV`: visible generator family A; visible ontology pool A.
- `SHADOW`: generator family B; ontology pool B; not used for direct tuning.
- `BLIND`: renderer family C + ontology pool C + task-schema family C. The exact blind generator and corpus are sealed before v3 implementation.

The blind corpus is stored outside normal repository source as a canonical sealed ZIP. GitHub stores only its hashes, counts, scorer contract, schema and freeze record until after the one-shot v3 evaluation.

## No gold-adjacent metadata

Runtime-visible case payload may contain only:
- user prompt;
- dialogue history;
- task-provided documents/facts/demonstrations;
- explicitly user-visible tables/graphs represented in the prompt itself.

Forbidden runtime inputs:
- `path_edges`;
- gold relation names;
- gold role labels;
- correct evidence IDs;
- answer indices;
- hidden `nota` flags;
- latent ontology IDs;
- split IDs;
- renderer IDs;
- proof paths.

Gold/provenance remain in scorer-only records.

## Case families

### 1. Semantic Rule Induction

Each episode introduces 1-4 nonce predicates or operators via natural-language demonstrations. The blind semantic universe must contain relation logics absent from DEV/SHADOW, including asymmetric, symmetric, transitive, anti-transitive, conditional and ternary-like compositions projected into binary queries.

Success requires inducing rule behavior, not mapping a nonce word to a familiar fixed relation label.

### 2. Surface Far Transfer

Every latent world is rendered using multiple independently authored surface families:
- active declarative;
- passive;
- nominalized relation;
- causal paraphrase;
- contrastive construction;
- subordinate clause;
- elliptical follow-up;
- reordered discourse.

Blind renderer templates share no normalized skeleton with DEV/SHADOW after entity/number/operator replacement.

### 3. Role / Voice / Coreference

Cases contain 2-5 entities and combinations of:
- active/passive voice;
- reversed mention order;
- pronouns and demonstratives;
- nominal anaphora;
- ellipsis;
- multiple plausible antecedents;
- clarification-required cases.

### 4. Task-Schema Induction

The model is shown demonstrations of a new task and must infer the output operation. Blind schemas include classification, ordered tuple extraction, set transformation, shortest proof choice, contradiction status, control action selection and minimal sufficient explanation.

No schema keyword used in DEV names the blind operation.

### 5. Compositional Reasoning

Blind episodes compose 2-5 newly introduced rules. Exact compositions are excluded from DEV/SHADOW. Queries include forward, inverse, blocked and NOTA cases.

### 6. Cross-Language Transfer

Instruction language, fact language and question language can differ. Distribution includes RU↔EN and a bounded RU↔KZ subset. Proper names and nonce operators are independent of language.

The score tracks retention relative to same-language controls.

### 7. Long-Horizon Transfer

Conversations are balanced across 30/50/75/100 turns and include:
- irrelevant topic segments;
- state updates;
- explicit corrections;
- temporary goals;
- suspended/resumed tasks;
- obsolete facts;
- controller disturbances;
- delayed query.

The unseen ontology is distinct from context/memory training families.

### 8. Evidence / Counterfactual

Cases require distinction between:
- support vs contradiction;
- independent vs copied evidence;
- sufficient vs insufficient evidence;
- actual vs counterfactual world;
- necessary vs sufficient cause;
- blocker/inhibitor;
- `UNRESOLVED` and `CONFLICTED` states.

## Paired invariance structure

At least 40% of applicable blind cases belong to semantic-equivalence groups with 2-4 different renderings. These enable:
- Paraphrase Invariance;
- Role Invariance;
- Language Retention;
- Counterfactual Consistency.

A model that answers only one surface realization correctly is penalized by the paired metric even if point accuracy is acceptable.

## Metrics

Primary:
- `FTX1 Macro Strict`: unweighted mean of eight track strict scores.
- `FTX1 Full Strict`: strict correct / 2400.
- `Far Transfer Ratio (FTR)`: blind macro / shadow macro.

Secondary:
- Generalization Gap = shadow macro - blind macro;
- Paraphrase Invariance;
- Role Invariance;
- Cross-Language Retention;
- Counterfactual Consistency;
- Abstention Precision/Recall;
- Hallucination Rate;
- Invalid Evidence/Citation Rate.

## Promotion gates for Unified v3

- FTX1 Macro Strict >= 75%;
- FTX1 Full Strict >= 75%;
- every track >= 60%;
- semantic_rule_induction >= 75%;
- surface_far_transfer >= 75%;
- task_schema_induction >= 65%;
- Paraphrase Invariance >= 85%;
- Role Invariance >= 85%;
- Cross-Language Retention >= 70%;
- Hallucination Rate <= 2%;
- Invalid Evidence/Citation Rate <= 1%;
- FTR >= 0.80;
- no post-blind tuning.

A high ID/shadow score cannot compensate for poor blind OOD.

## Pre-freeze red-team veto

FTX1 cannot be frozen unless all veto tests pass:

1. regex/template baseline <= 40% Full Strict;
2. bag-of-words nearest-template baseline <= 45%;
3. answer-position/frequency baseline near chance and <= 30%;
4. metadata-only baseline <= 20%;
5. dev-template matcher <= 45% on blind candidate;
6. blind normalized skeleton overlap with DEV <= 5%;
7. blind normalized skeleton overlap with SHADOW <= 5%;
8. no forbidden gold-adjacent runtime fields;
9. paired semantic variants have identical gold semantics;
10. changing surface without changing latent world does not change gold;
11. perturbing the latent rule/world while preserving surface style changes gold when expected.

If any veto fails, the candidate blind suite is destroyed and regenerated with a new seed/family before v3 work begins.

## Scoring contract

Runtime emits a normalized response object:

```python
@dataclass(frozen=True)
class FTXPrediction:
    answer: str | None
    structured: tuple[str, ...] = ()
    epistemic: str | None = None
    abstain: bool = False
    citations: tuple[str, ...] = ()
```

Each case owns a scorer-only semantic contract. String exact-match is used only where the task explicitly demands a fixed token/schema. Otherwise canonical semantic scoring is used.

## Anti-leakage rules

- Blind exact generator source is not placed in the v3 development branch.
- Blind corpus is not searchable by v3 code.
- No case IDs encode track, split, renderer or gold.
- Entity/operator namespaces are shared in statistical form across splits but values do not identify split.
- DEV/SHADOW/BLIND seeds are independent.
- Blind renderer vocabulary and syntax families are held out.
- Any inspection of blind content before v3 preblind freeze invalidates FTX1 and requires FTX2.

## Freeze sequence

1. Commit this design/preregistration.
2. Implement public schema/scorer/validators via TDD.
3. Implement DEV and SHADOW generators.
4. Implement sealed blind generator in an isolated freeze workspace.
5. Generate candidate blind 2400.
6. Run structural validators and red-team baselines.
7. If any veto fails: destroy candidate and regenerate; no v3 code allowed.
8. Freeze canonical blind ZIP + SHA-256 + per-track hashes.
9. Commit only public code + freeze manifest/hash to `nexus-ftx1-freeze-v1`.
10. Create `unified-v3-generalization-first` only from the post-freeze commit.

## Scientific boundary

FTX1 remains synthetic/semi-synthetic. Passing it does not establish unrestricted AGI. Its purpose is narrower: provide materially stronger evidence of distributional generalization and far transfer than UB1/UB2, with explicit defenses against template memorization.
