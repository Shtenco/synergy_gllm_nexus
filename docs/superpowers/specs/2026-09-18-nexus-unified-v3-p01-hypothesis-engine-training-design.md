# NEXUS Unified v3 P0.1 Hypothesis Engine + Synthetic Training Design

**Status:** APPROVED DESIGN / PRE-IMPLEMENTATION  
**Date:** 2026-09-18  
**Branch:** `unified-v3-generalization-first`  
**Parent checkpoint:** `e75aec5b7266876171ca30964309c99afe58283c`  
**Compatibility:** all P0 contracts and regression tests remain mandatory  
**Scientific constraint:** FTX1 BLIND remains sealed and is not used for implementation, tuning, curriculum design, model selection, or early stopping.

## 1. Objective

P0.1 upgrades Unified v3 from a proof-of-architecture into a bounded adaptive hypothesis engine.

The system must no longer assume that one parsed world and one inferred rule set are immediately correct. It must maintain competing world/rule hypotheses, predict consequences, compare them with new evidence, revise rankings, branch on genuine ambiguity, preserve contradictions as structured state, and answer only when the surviving hypothesis mass licenses an epistemic conclusion.

The first training stage is performed immediately after the symbolic P0.1 engine is implemented and verified. Training uses independent synthetic universes generated specifically for meta-generalization, never FTX1 BLIND.

The central scientific target is:

> learn to discover transferable laws of unfamiliar worlds, not memorize benchmark relation names or surface forms.

## 2. Architectural invariant

P0's hard representation bottleneck remains unchanged:

```text
Surface -> Semantic IR -> Hypothesis Engine -> Task Program
        -> Executor -> Epistemic Consensus -> Generalization Audit -> Renderer
```

Raw prompt/history/document text does not enter hypothesis search, rule execution, epistemic consensus, or counterfactual execution.

P0.1 adds a new internal level:

```text
Semantic Observations
    -> Candidate Worlds
    -> Candidate Rule Programs
    -> Hypothesis Beam
    -> Predict / Compare / Rescore / Prune / Fork
```

A hypothesis is a typed latent model of the current universe, not a textual explanation.

## 3. Backward compatibility

The following P0 properties are regression gates and may not regress:

1. materially different controlled surfaces can normalize to equivalent semantics;
2. true role swaps change semantics;
3. anonymous operator induction survives entity/operator renaming;
4. non-transitive negative controls block unconditional transitivity;
5. the executor receives no raw text;
6. bounded multi-hop execution retains derivation provenance;
7. `PROVED / DISPROVED / UNRESOLVED / CONFLICTED` reach the renderer faithfully;
8. generalization auditing checks both invariance and intervention sensitivity.

No P0 test may be deleted or weakened to make P0.1 pass.

## 4. Hypothesis state

Introduce a typed `HypothesisState`:

```python
HypothesisState(
    hypothesis_id,
    world,
    rules,
    score,
    complexity_cost,
    contradiction_cost,
    prediction_score,
    evidence_mass,
    lineage,
    status,
)
```

`status` is one of:

```text
ACTIVE
PRUNED
FALSIFIED
DOMINATED
FORKED
```

A `HypothesisBeam` owns a bounded tuple of active hypotheses plus eliminated-hypothesis trace records.

### 4.1 Score semantics

The exact scalar schedule is implementation-configurable, but the ranking must decompose into explicit terms:

```text
score =
    explained_observations
  + confirmed_predictions
  + independent_evidence
  - contradictions
  - failed_predictions
  - complexity_penalty
```

No score term may depend on surface renderer ID, split ID, case ID, benchmark track, answer position, or hidden gold metadata.

### 4.2 Simplicity prior

If two hypotheses explain exactly the same evidence, the simpler hypothesis is preferred.

Complexity is measured structurally from rule AST size, condition count, exception count, and latent branches. Operator names and entity names do not affect complexity.

## 5. Beam search and revision

Add `HypothesisSearch` with deterministic bounded search for P0.1.

Inputs:

```text
WorldCandidates
RuleCandidates
Observations
beam_width
```

Outputs:

```text
HypothesisBeam
```

Default P0.1 beam width: 8.

Required operations:

- seed candidate hypotheses;
- score candidates;
- deduplicate structurally equivalent hypotheses;
- retain ties when evidence is insufficient;
- prune dominated hypotheses;
- falsify directly contradicted hypotheses;
- fork hypotheses when an observation admits materially different interpretations;
- rescore after every new observation;
- preserve lineage so a later result can explain which theory survived and why.

Beam width is a resource cap, not semantic evidence.

## 6. Typed rule algebra

Replace property-only reasoning with an explicit rule AST while keeping P0 `RuleProgram.has_property()` compatibility.

Introduce primitives:

```text
AtomPattern
Variable
RuleCondition
RuleBlocker
RuleClause
RuleProgram
```

A rule conceptually has:

```text
antecedents
conditions
blockers
consequent
priority
confidence
provenance
```

P0.1 candidate rule families:

- DIRECT;
- SYMMETRIC;
- ASYMMETRIC;
- TRANSITIVE;
- ANTI_TRANSITIVE;
- INVERSE;
- COMPOSITION;
- CONDITIONAL;
- BLOCKED;
- TEMPORAL_REPLACEMENT.

Examples:

```text
R(x,y) -> R(y,x)
R(x,y) & R(y,z) -> R(x,z)
A(x,y) & B(y,z) -> C(x,z)
A(x,y) & State(y,OPEN) -> B(x,y)
A(x,y) & !Blocked(y) -> B(x,y)
```

Unknown operator symbols remain anonymous. The rule inducer infers rule shape; it does not map nonce tokens to a fixed ontology label.

## 7. Candidate rule induction

`RuleInducer` becomes a hypothesis generator rather than a single-rule selector.

For each episode it must:

1. construct all candidate rule families permitted by the current typed observations;
2. score how many demonstrations each rule explains;
3. record contradictions;
4. reserve held-out demonstrations when possible;
5. rank by predictive fit and simplicity;
6. emit multiple candidates when underdetermined.

A candidate that explains past observations but fails held-out prediction must lose score.

The engine therefore optimizes explanatory + predictive power, not retrospective fit only.

## 8. Prediction ledger

Every active hypothesis can emit predictions.

Introduce:

```text
Prediction(
    prediction_id,
    hypothesis_id,
    atom,
    expected_polarity,
    derivation,
    created_at,
    resolved_at,
    outcome,
)
```

`outcome`:

```text
PENDING
CONFIRMED
REFUTED
UNOBSERVED
```

When a new observation arrives, the ledger resolves matching predictions and updates the parent hypothesis score.

A failed prediction is distinct from an explicit logical contradiction and receives its own penalty.

## 9. Competing world hypotheses

`WorldInducer` may emit more than one `WorldHypothesis`.

Ambiguous observations may produce alternative bindings or state assignments.

Each world must carry:

- facts;
- temporal state;
- contradiction sets;
- unresolved alternatives;
- provenance;
- parent world ID;
- intervention lineage if counterfactual.

Equivalent worlds are canonicalized and deduplicated by semantic fingerprint.

## 10. Temporal revision ledger

Introduce immutable `TemporalFact` / `FactVersion` records.

Lifecycle states:

```text
ACTIVE
SUPERSEDED
RETRACTED
TEMPORARY
CONDITIONAL
```

Each fact version stores:

- `valid_from`;
- `valid_until`;
- `supersedes`;
- provenance;
- polarity;
- lifecycle status.

A later correction creates a new version and marks the old version superseded rather than deleting history.

P0.1 must answer both:

```text
CURRENT_STATE
HISTORICAL_STATE
```

without conflating the two.

## 11. Contradiction engine

Contradictions are first-class data.

Introduce `ConflictSet`:

```text
positive_support
negative_support
independence_groups
temporal_order
provenance
resolution_status
```

Possible resolution statuses:

```text
UNRESOLVED
CONFLICTED
SUPERSEDED
RESOLVED_POSITIVE
RESOLVED_NEGATIVE
```

A contradiction never becomes certainty merely because one side was processed later, unless temporal semantics explicitly define supersession.

## 12. Counterfactual worlds

Introduce `Intervention` and `CounterfactualEngine`.

The engine clones an actual `WorldHypothesis` into a derived world and applies one or more typed interventions:

```text
ADD_FACT
REMOVE_FACT
FLIP_POLARITY
SET_STATE
BLOCK_RULE
ENABLE_RULE
```

The actual world is immutable.

After intervention, the normal executor reruns on the counterfactual world.

A `CounterfactualComparison` records:

- actual result;
- counterfactual result;
- changed facts;
- changed derivations;
- whether the target conclusion changed;
- minimal changed support when available.

This supports future necessary/sufficient-cause analysis without relying on causal vocabulary in surface text.

## 13. Rich task IR

Extend `TaskOpcode` while preserving `QUERY_RELATION`.

P0.1 opcodes:

```text
QUERY_RELATION
SELECT_ENTITY
EXTRACT_SET
ORDER_TUPLE
EPISTEMIC_STATUS
FIND_PROOF
FIND_MINIMAL_PROOF
COMPARE_WORLDS
COUNTERFACTUAL_QUERY
CURRENT_STATE
HISTORICAL_STATE
```

`TaskInducer` receives structured task examples and emits one or more candidate `TaskProgram` objects with confidence.

If two task schemas remain equally plausible, the runtime remains `UNRESOLVED`; it does not guess based on familiar benchmark wording.

## 14. Executor P0.1

The executor becomes a typed bounded rule engine.

It must support:

- direct facts;
- symmetry;
- inverse;
- transitivity;
- heterogeneous operator composition;
- conditions;
- blockers;
- temporal validity filters;
- explicit negative facts;
- proof-path enumeration;
- minimal proof selection;
- bounded search depth;
- counterfactual world execution.

Every derived fact records:

```text
parents
rule_id
hypothesis_id
world_id
depth
temporal_context
```

The executor still receives no raw text.

## 15. Epistemic consensus across hypotheses

The epistemic controller resolves results over the active beam, not only one execution.

Each hypothesis contributes weighted support according to normalized hypothesis score and evidence quality.

Core behavior:

- strong aligned support -> `PROVED`;
- strong aligned negative support -> `DISPROVED`;
- insufficient mass -> `UNRESOLVED`;
- materially supported positive and negative conclusions -> `CONFLICTED`.

P0.1 default conservative thresholds are config values, not hard-coded benchmark constants.

The controller must expose:

```text
support_mass
contradiction_mass
unresolved_mass
dominant_hypotheses
```

so confidence has interpretable meaning.

## 16. Generalization Governor v2

Extend the current governor from answer stability to model stability.

Audits:

- paraphrase invariance;
- active/passive invariance;
- mention-order invariance;
- entity rename invariance;
- operator rename invariance;
- fact-order invariance;
- irrelevant distractor robustness;
- cross-language semantic equivalence when available;
- expected-change intervention sensitivity;
- hypothesis-shape stability.

New metric:

```text
Hypothesis Stability Score
```

This compares rule/world structural fingerprints across semantics-preserving universe transformations.

A model that always emits the same answer fails intervention sensitivity even if invariance is perfect.

## 17. Synthetic universe generator

Training must not use FTX1 BLIND.

Create an independent generator under:

```text
training/v3_meta/
```

It samples synthetic universes with independent seeds and namespaces.

Each universe samples:

- 4-20 entities;
- 1-6 anonymous operators;
- rule algebra from the P0.1 rule families;
- 1-5 rule clauses;
- positive/negative facts;
- optional conflicts;
- optional temporal revisions;
- optional blockers;
- optional conditional state;
- optional counterfactual query;
- task schema;
- language/surface renderer family;
- distractor density.

Every universe has a latent program known only to the generator/scorer.

The runtime receives only permitted surface/structured task inputs.

## 18. Train/dev/OOS partition

Synthetic meta-training uses three disjoint generator families:

```text
META-TRAIN A
META-DEV B
META-OOS C
```

They differ in:

- operator namespaces;
- entity namespaces;
- rule compositions;
- renderer families;
- task schema combinations;
- distractor distributions;
- conflict patterns.

META-OOS C is never used for gradient updates or threshold tuning.

FTX1 SHADOW remains a separate audit instrument and is not converted into a training split.

FTX1 BLIND remains sealed.

## 19. Training curriculum

Training begins only after symbolic P0.1 tests pass.

Stage 0 — symbolic oracle validation:
- generate small universes;
- verify latent rule program and executor/scorer agree;
- reject generator families with ambiguity not represented in gold.

Stage 1 — semantic invariance:
- entity/operator renaming;
- active/passive/reordered surfaces;
- equivalent paraphrase pairs;
- objective: equivalent latent semantic/world fingerprints.

Stage 2 — single-rule induction:
- symmetry;
- inverse;
- transitivity;
- anti-transitivity;
- blockers;
- conditions.

Stage 3 — multi-rule composition:
- heterogeneous composition;
- 2-5 inference steps;
- held-out operator combinations.

Stage 4 — hypothesis revision:
- early evidence supports multiple theories;
- later evidence discriminates them;
- train ranking change and prediction-ledger accuracy.

Stage 5 — temporal/conflict:
- corrections;
- supersession;
- conflicting sources;
- historical/current queries.

Stage 6 — counterfactual:
- single interventions;
- proof-path changes;
- necessary-support detection.

Stage 7 — mixed OOS episodes:
- unseen ontology;
- unseen operator composition;
- unseen surface renderer;
- unseen task combination.

## 20. Learned component boundary

P0.1 symbolic search remains the authoritative reference implementation.

The first learned component is not allowed to bypass contracts. It may learn one or more of:

- hypothesis ranking;
- rule candidate proposal;
- semantic alignment;
- task-program ranking.

Its output is always a typed proposal consumed by the symbolic engine.

The learned model cannot directly write the final answer.

This preserves auditability and permits ablation against the deterministic baseline.

## 21. Training objective

The first learned ranker uses multi-objective loss.

Required objective terms:

- correct hypothesis ranking;
- held-out prediction accuracy;
- semantic invariance across paired surfaces;
- entity/operator rename invariance;
- intervention sensitivity;
- task-program correctness;
- calibration/abstention quality;
- complexity regularization;
- penalty for surface-feature dependence.

Training reports must separate:

```text
in-distribution accuracy
META-DEV accuracy
META-OOS accuracy
generalization gap
hypothesis stability
prediction accuracy
calibration
```

No single aggregate score can hide catastrophic OOS failure.

## 22. Training data anti-leak rules

Forbidden in learned features:

- generator family ID;
- split ID;
- case ID patterns;
- latent rule names;
- gold proof path;
- answer index;
- renderer ID;
- target hypothesis rank;
- hidden task opcode;
- FTX1 metadata.

Random seeds and latent gold stay scorer-side.

Operator/entity tokens must be randomized frequently enough that memorizing token identity is non-competitive.

## 23. Training scale for first pass

The first P0.1 training run is intentionally bounded and diagnostic.

Target initial corpus:

```text
META-TRAIN: 50,000 episodes
META-DEV:   5,000 episodes
META-OOS:   5,000 episodes
```

If local compute is insufficient, the implementation may begin with 10,000 / 1,000 / 1,000 but the report must label that run as a smoke-training run, not the full first-pass target.

No FTX1 BLIND evaluation is part of this training.

## 24. Training checkpoints

Persist:

- source commit SHA;
- generator config hash;
- corpus manifest hash;
- model/ranker config;
- random seeds;
- checkpoint hash;
- train/dev/OOS metrics;
- ablation metrics;
- anti-leak scan result.

Model selection uses META-DEV only.

META-OOS is reported after checkpoint selection.

## 25. P0.1 acceptance gates

P0.1 symbolic engine gates:

1. all P0 tests pass unchanged;
2. at least two competing hypotheses survive an intentionally underdetermined episode;
3. a discriminating observation reverses or materially changes hypothesis ranking;
4. entity/operator rename preserves hypothesis structural ranking;
5. symmetric and inverse rules are distinguished;
6. heterogeneous composition executes correctly;
7. blocker/conditional rules suppress invalid derivations;
8. temporal correction preserves history while changing current state;
9. conflict remains structured and does not collapse to certainty;
10. counterfactual intervention changes only the cloned world;
11. richer task programs are induced without benchmark track labels;
12. executor still rejects raw text.

First training gates:

1. synthetic train/dev/OOS families are disjoint by construction;
2. a frequency/template baseline is materially below the trained ranker on META-OOS;
3. META-OOS hypothesis-selection accuracy exceeds chance by a substantial margin;
4. rename invariance >= 95% on synthetic paired controls;
5. hypothesis stability >= 90% on semantics-preserving paired controls;
6. expected-change intervention sensitivity >= 90%;
7. generalization gap is reported explicitly;
8. no training result is called successful if META-TRAIN rises while META-OOS collapses.

These thresholds are development gates for the synthetic curriculum, not substitutes for FTX1 promotion gates.

## 26. Failure behavior

Fail closed when:

- task schema is underdetermined;
- hypothesis mass is fragmented;
- positive/negative support is materially conflicted;
- counterfactual intervention produces an invalid world;
- temporal query lacks a resolvable time scope;
- rule search reaches resource bounds without stable consensus;
- learned ranker disagrees sharply with symbolic evidence and no hypothesis dominates.

The runtime returns an epistemic unresolved/conflicted result with trace reasons rather than guessing.

## 27. Proposed code structure

```text
src/nexus_gllm/unified_v3/
    contracts.py
    hypotheses.py
    rule_algebra.py
    rule_induction.py
    hypothesis_search.py
    prediction.py
    world.py
    temporal.py
    conflicts.py
    counterfactual.py
    task_induction.py
    executor.py
    epistemic.py
    generalization.py
    runtime.py
    training_adapters.py

training/v3_meta/
    universe.py
    rule_sampler.py
    renderer.py
    tasks.py
    dataset.py
    scorer.py
    ranker.py
    train.py
    evaluate.py

tests/unified_v3/
    existing P0 tests unchanged
    test_hypothesis_beam.py
    test_rule_algebra.py
    test_prediction_revision.py
    test_temporal_revision.py
    test_conflicts.py
    test_counterfactual.py
    test_rich_task_induction.py
    test_epistemic_consensus.py
    test_hypothesis_stability.py
    test_p01_runtime.py

tests/v3_meta/
    test_generator_separation.py
    test_generator_gold_consistency.py
    test_training_features_no_leak.py
    test_ranker_smoke.py
    test_meta_oos_eval.py
```

## 28. Implementation order

The implementation plan must use strict TDD in this order:

1. extend contracts compatibly;
2. rule AST/algebra;
3. hypothesis beam/search;
4. prediction ledger and revision;
5. temporal ledger;
6. contradiction engine;
7. counterfactual engine;
8. rich task IR;
9. executor extensions;
10. epistemic beam consensus;
11. Generalization Governor v2;
12. P0.1 runtime integration;
13. synthetic universe generator;
14. train/dev/OOS separation tests;
15. baseline ranker and anti-shortcut baselines;
16. bounded first training run;
17. META-OOS evaluation;
18. verification report and checkpoint hashes.

## 29. Definition of done

P0.1 is not complete merely because additional rule families exist.

It is complete only when a fresh automated episode demonstrates the full scientific loop:

```text
underdetermined observations
-> multiple live hypotheses
-> predictions
-> new discriminating evidence
-> hypothesis reranking
-> temporal/conflict-aware world update
-> typed task execution
-> counterfactual intervention
-> epistemic consensus
-> generalization stability audit
```

and the same latent process remains structurally equivalent after systematic renaming of entities/operators and semantics-preserving surface changes.

The first training milestone is complete only when a reproducible checkpoint and corpus manifest exist and META-OOS results are reported separately from training performance.
