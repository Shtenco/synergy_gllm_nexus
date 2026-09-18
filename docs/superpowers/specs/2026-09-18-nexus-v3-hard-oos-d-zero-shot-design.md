# NEXUS Unified v3 HARD-OOS D Zero-Shot Design

**Status:** APPROVED DESIGN / PRE-IMPLEMENTATION  
**Date:** 2026-09-18  
**Branch:** `unified-v3-generalization-first`  
**Frozen checkpoint under test:** `artifacts/v3_meta/p01_first_hard/ranker.pt`  
**Frozen checkpoint SHA-256:** `95fd54d5036c7dfda0da1b9edbff5b804e6fa7163aab2fec83459075eb3b2c96`  
**Parent branch checkpoint:** `ccaf9dc19733ed43d458a5e522373d391aa81cf6`

## 1. Purpose

HARD-OOS D is a one-shot falsification instrument for Unified v3 P0.1.

Its purpose is not to produce another high synthetic score. It is designed to determine whether the frozen P0.1 hypothesis ranker and symbolic reasoning stack transfer to a materially different generator family with unfamiliar rule-AST topologies, partial/noisy demonstrations, adversarial distractors, ambiguous bindings, temporal gates, inhibitors, and counterfactual traps.

D is consumed exactly once by the frozen checkpoint before any D-informed retraining.

## 2. Scientific isolation

D is implemented under:

```text
training/v3_hard_oos_d/
```

It MUST NOT import generator logic from:

```text
training/v3_meta/universe.py
training/v3_meta/rule_sampler.py
```

Neutral shared contracts, hashing utilities, and scoring helpers are permitted only when they do not encode A/B/C generator assumptions.

D must have:

- independent RNG namespace;
- independent AST sampler;
- independent world sampler;
- independent distractor generator;
- independent binding ambiguity generator;
- independent temporal/inhibitor generator;
- independent counterfactual trap generator;
- independent manifest and scoring pipeline.

The existing checkpoint and source are frozen before D generation.

## 3. One-shot protocol

Execution order is mandatory:

```text
freeze current checkpoint/source/config
-> build D generator
-> validate generator internally
-> generate D corpus
-> seal manifest + corpus hashes
-> evaluate frozen ranker zero-shot
-> evaluate symbolic/simple baselines
-> write report
-> only then inspect failures for future training design
```

No gradient update, threshold change, feature change, rule change, or model-selection step is permitted between D sealing and zero-shot reporting.

If any implementation bug in the D generator itself is found after corpus sealing, the sealed D instance is invalidated and regenerated under a new manifest version before evaluation.

## 4. HARD-OOS D corpus

Initial target:

```text
10,000 episodes
```

Strata:

```text
novel_ast             2,000
partial_noisy         1,500
binding_ambiguity     1,500
temporal_inhibitor    1,500
counterfactual_traps  1,500
mixed_adversarial     2,000
```

Every episode has a stratum label scorer-side only. The frozen ranker does not receive the stratum ID.

## 5. Latent program representation

Unlike A/B/C, D does not define the target as one of four fixed rule labels.

The gold object is a typed latent program AST.

Required node families:

```text
ATOM
AND
NOT
IMPLIES
COMPOSE
INVERSE
SYMMETRIC
TEMPORAL_BEFORE
TEMPORAL_AFTER
STATE_GATE
INHIBITOR
EXCEPTION
COUNTERFACTUAL_INTERVENTION
```

Example programs:

```text
A(x,y) AND B(y,z) -> C(x,z)
```

```text
A(x,y) AND B(y,z) AND State(z,OPEN) AND NOT Blocked(y)
-> C(x,z)
```

```text
A(x,y,t1) AND t2 > t1 AND NOT Disable(x,t1,t2)
-> B(y,x,t2)
```

```text
A(x,y) AND B(y,z) -> C(x,z)
C(x,z) AND Inhibitor(z) -> NOT D(x,z)
```

Operator symbols and entity names are nonce/randomized and have no semantic meaning.

## 6. Novel AST topology gate

D must contain rule topologies never present in the A/B/C training generator.

Minimum required held-out structures:

- heterogeneous 2-operator composition;
- 3-antecedent conjunction;
- nested condition + inhibitor;
- temporal gate + relation consequence;
- composition followed by inhibition;
- exception override;
- two-stage rule chain whose intermediate operator is never directly queried;
- counterfactual intervention over a derived intermediate state.

A topology fingerprint is computed from node types and arities only; operator/entity tokens are excluded.

A validation test must prove that D topology fingerprints are disjoint from those expressible by the original A/B/C candidate family.

## 7. Partial and noisy demonstrations

For `partial_noisy` and `mixed_adversarial`:

- hide 20-50% of potentially informative observations;
- inject 10-30% irrelevant observations;
- inject 0-15% noisy observations;
- preserve enough evidence for the gold epistemic state to be known by the scorer.

Noise may create ambiguity. In those episodes the correct target can be `UNRESOLVED` rather than an arbitrary single theory.

The scorer must distinguish true ambiguity from generator corruption.

## 8. Adversarial distractors

Distractors are not IID random facts.

Required distractor patterns:

- apparent transitivity that fails under a hidden state gate;
- apparent symmetry broken by one inhibitor;
- apparent inverse relation caused by entity-role swap;
- high-frequency relation that is never causally relevant;
- shortcut feature correlated with the target in early examples and reversed later;
- copied evidence that should not count as independent support;
- temporal fact that is valid historically but superseded in current state.

A simple single-feature baseline must not solve D.

## 9. Binding ambiguity

D must contain episodes where multiple entity/role bindings are initially compatible.

The episode supplies later discriminating evidence in some cases, while other cases remain genuinely ambiguous.

Required outcomes:

- rank-order change when evidence disambiguates;
- multiple live hypotheses when evidence remains insufficient;
- `UNRESOLVED` when no hypothesis reaches the epistemic threshold.

Correct behavior is not forced commitment.

## 10. Temporal/inhibitor stratum

Temporal episodes include:

- fact activation windows;
- supersession;
- retraction;
- temporary state;
- ordered events;
- rule activation only before/after an event;
- inhibitors that block a rule during a time interval.

Queries distinguish:

```text
CURRENT_STATE
HISTORICAL_STATE
RELATION_AT_TIME
```

A current-state answer derived from superseded evidence is scored incorrect.

## 11. Counterfactual trap stratum

Counterfactual episodes require intervention on exactly one typed cause/state/rule gate.

Traps include:

- removing an irrelevant fact should not change the conclusion;
- removing a necessary support should change it;
- removing one of two redundant supports should not change it;
- flipping a blocker should enable a previously impossible conclusion;
- changing a temporal gate outside the relevant interval should not change the answer;
- intervention on a copied evidence source should not behave like deleting independent support.

The actual world remains immutable.

## 12. Mixed adversarial stratum

`mixed_adversarial` combines at least four of:

- novel AST;
- partial evidence;
- noise;
- binding ambiguity;
- adversarial distractor;
- temporal condition;
- inhibitor;
- counterfactual intervention.

The goal is to prevent success through isolated feature recognition.

## 13. Frozen ranker adapter

The P0.1 ranker expects an 8-dimensional structural candidate vector.

D therefore has two evaluation modes.

### 13.1 Compatibility zero-shot

A frozen adapter computes the same eight permitted structural channels without exposing D gold metadata:

```text
explained
contradictions
heldout
complexity
symmetry_signal
chain_signal
inverse_signal
blocker_signal
```

The formulas are frozen before D corpus sealing.

No new D-specific feature enters the checkpoint.

### 13.2 Full reasoning zero-shot

The symbolic P0.1 engine is evaluated on D episodes using typed observations/worlds/rules/tasks.

This separates:

- whether the learned ranker transfers;
- whether the symbolic reasoning architecture transfers.

If the ranker cannot represent a novel D AST at all, this is recorded as an explicit `representation_failure`, not silently mapped to the nearest known class.

## 14. Baselines

Required D baselines:

- random candidate;
- simplicity-only;
- explained-only;
- contradiction-only;
- nearest known A/B/C family;
- always-transitive;
- symbolic candidate search without learned ranker when representable.

No baseline may access D gold AST except through final scorer comparison.

## 15. Metrics

Report at minimum:

```text
answer_accuracy
ast_topology_exact
ast_topology_partial
hypothesis_ranking_accuracy
prediction_accuracy
counterfactual_accuracy
temporal_accuracy
inhibitor_accuracy
binding_resolution_accuracy
abstention_accuracy
rename_invariance
hypothesis_stability
theory_revision_score
calibration_ece
representation_failure_rate
```

All metrics are also broken down by stratum.

No aggregate metric may hide a catastrophic stratum failure.

## 16. Theory Revision Score

For episodes with staged evidence:

1. record hypothesis ranking before discriminating evidence;
2. apply discriminating evidence;
3. record ranking after evidence;
4. compare against scorer-side expected ranking movement.

The score rewards:

- preserving multiple theories while evidence is insufficient;
- promoting the correct theory after discriminating evidence;
- demoting/refuting theories contradicted by new observations;
- avoiding overreaction to irrelevant distractors.

## 17. Rename invariance

Each eligible D episode has a paired transformed twin with:

- all entity IDs renamed;
- all operator IDs renamed;
- fact order permuted;
- surface-equivalent ordering changes where applicable.

The latent program topology remains unchanged.

Required metric:

```text
rename_invariance
```

A model that succeeds on the original but changes theory structure after renaming fails the pair.

## 18. Acceptance thresholds

The following are strong-result gates, not guaranteed expected outcomes:

```text
answer_accuracy          >= 0.70
ast_topology_exact       >= 0.60
counterfactual_accuracy  >= 0.70
temporal_accuracy        >= 0.65
inhibitor_accuracy       >= 0.65
rename_invariance        >= 0.95
hypothesis_stability     >= 0.85
calibration_ece          <= 0.10
```

Additionally:

- learned ranker must materially outperform explained-only and simplicity baselines;
- mixed_adversarial performance must be reported independently;
- representation failures must not be excluded from denominators;
- excessive confident wrong answers fail the calibration gate even if raw accuracy is high.

A score below these thresholds is a valid scientific result and must not be hidden or tuned away.

## 19. Consumption discipline

After the first D zero-shot report:

- D is considered consumed for future model tuning;
- D failures may be used to design a new training family E;
- any model trained or tuned using D cannot claim D as OOS;
- the next clean far-transfer evaluation must use a newly authored family F or later.

## 20. Manifest and hashes

Before running the frozen checkpoint, persist:

- generator source commit SHA;
- generator config;
- generator version;
- RNG seed;
- episode count per stratum;
- topology fingerprint inventory;
- corpus SHA-256;
- scorer SHA-256;
- adapter SHA-256;
- frozen model SHA-256;
- frozen source commit SHA.

The manifest itself receives a SHA-256.

## 21. Anti-leak rules

Runtime/model-visible input MUST NOT contain:

- stratum ID;
- generator version/family ID;
- episode index pattern that reveals stratum;
- gold AST;
- gold topology fingerprint;
- expected ranking;
- gold proof;
- answer index;
- target epistemic state;
- counterfactual gold result;
- scorer-only temporal labels.

Episode IDs are random opaque identifiers.

## 22. Test strategy

Strict TDD.

Required tests before generator implementation:

- D does not import A/B/C generator logic;
- topology fingerprints are disjoint from A/B/C;
- stratum counts equal 10,000 target allocation;
- runtime-visible records contain no scorer-only fields;
- rename twins preserve gold topology;
- counterfactual interventions do not mutate actual world;
- partial/noisy episodes remain scorer-valid;
- ambiguity episodes can legitimately target `UNRESOLVED`;
- single-feature baselines remain below shortcut veto thresholds;
- model checkpoint hash matches the frozen P0.1 ranker before evaluation;
- evaluation code contains no optimizer/gradient step.

## 23. Output artifacts

Planned output:

```text
training/v3_hard_oos_d/
    ast.py
    generator.py
    strata.py
    distractors.py
    bindings.py
    temporal.py
    counterfactual.py
    adapter.py
    scorer.py
    evaluate.py
    baselines.py

artifacts/v3_hard_oos_d/
    manifest.json
    corpus_summary.json
    topology_inventory.json
    zero_shot_metrics.json
    baseline_metrics.json

docs/results/
    2026-09-18-nexus-v3-hard-oos-d-zero-shot-report.md
```

The complete 10,000-episode corpus need not be committed if it is large; its canonical hash and reproducible generator manifest must be committed.

## 24. Definition of done

HARD-OOS D is complete only when:

1. the independent D generator passes anti-leak and structural-independence tests;
2. the 10,000-episode corpus is generated and sealed before model evaluation;
3. frozen checkpoint SHA exactly matches the pre-D checkpoint;
4. no training/update occurs during D evaluation;
5. zero-shot ranker and symbolic results are reported by stratum;
6. baselines are reported beside model results;
7. rename invariance and theory revision are measured;
8. representation failures remain visible;
9. D is marked consumed after report generation;
10. FTX1 BLIND remains unopened.
