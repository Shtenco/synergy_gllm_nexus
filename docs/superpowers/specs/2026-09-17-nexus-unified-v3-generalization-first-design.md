# NEXUS Unified v3 Generalization-First Design

**Status:** APPROVED FOR SPECIFICATION / PRE-IMPLEMENTATION  
**Date:** 2026-09-17  
**Branch:** `unified-v3-generalization-first`  
**Parent scientific gate:** NEXUS-FTX1 frozen before v3 implementation  
**Compatibility baseline:** Unified v2 remains immutable and is used as donor/regression reference only

## 1. Purpose

Unified v3 exists to solve a different problem than prior NEXUS generations.

The objective is not to maximize score on known benchmark families. The objective is to construct a runtime that can preserve semantics and induce task structure when the surface form, ontology, relation names, operator vocabulary, output schema, language, discourse order, and local world rules change.

The system must therefore survive a change of the task universe rather than merely recognize a familiar template.

The first implementation target, `Unified v3 P0`, is a minimal architectural proof, not a large neural model. P0 must demonstrate two properties before any scale-up work is allowed:

1. semantically equivalent surface forms map to the same or equivalent latent world representation;
2. a previously unseen relation/operator can be induced from demonstrations without relying on a pre-registered relation label.

Everything in this design serves those two properties.

## 2. Core architectural decision

The central invariant of v3 is:

> Downstream reasoning does not receive raw user text.

Raw prompt text, dialogue strings, document strings, language-specific morphology and renderer identifiers terminate at the surface/semantic boundary. Reasoning modules consume typed semantic structures only.

This creates a hard representation bottleneck:

```text
Surface Input
    -> Surface Adapter / Semantic Parser
    -> Semantic IR
    -> World Hypotheses
    -> Latent Rule Program
    -> Task Program
    -> Compositional Execution
    -> Epistemic Result
    -> Surface Realization
```

The goal is to make benchmark shortcutting structurally difficult. A downstream executor cannot exploit lexical artifacts if its interface does not contain text.

## 3. Non-goals for P0

P0 does not attempt to be a complete conversational LLM, a universal neural foundation model, a production multilingual assistant, or a drop-in replacement for every Unified v2 organ.

P0 also does not optimize directly against FTX1 BLIND. BLIND content, BLIND generator source and BLIND gold remain sealed until a preblind v3 artifact is frozen.

P0 is specifically a falsifiable architecture prototype for semantic invariance, latent rule induction, task induction, compositional execution and epistemic discipline.

## 4. Repository isolation

All new implementation lives under:

```text
src/nexus_gllm/unified_v3/
```

Unified v2 source is not edited for v3 feature work.

Allowed interaction with v2 is one-way through explicit adapters. This protects the v2 regression baseline and prevents accidental mutation of historical behavior.

Proposed initial package layout:

```text
src/nexus_gllm/unified_v3/
    __init__.py
    contracts.py
    semantic_ir.py
    surface.py
    role_binding.py
    world.py
    rule_induction.py
    task_induction.py
    executor.py
    epistemic.py
    temporal.py
    counterfactual.py
    generalization.py
    renderer.py
    runtime.py
    adapters/
        v2_donors.py

tests/unified_v3/
    test_semantic_ir.py
    test_surface_invariance.py
    test_role_binding.py
    test_world_hypotheses.py
    test_rule_induction.py
    test_task_induction.py
    test_executor.py
    test_epistemic.py
    test_temporal.py
    test_counterfactual.py
    test_generalization_governor.py
    test_runtime_p0.py
```

P0 may implement only the files required for the first vertical slice. The package boundaries are architectural contracts, not a requirement to fill every file immediately.

## 5. Semantic IR

`Semantic IR` is the only reasoning-facing representation of language-derived information.

It must support at minimum:

- entities;
- mentions and aliases;
- semantic roles;
- predicates/operators;
- events;
- states;
- temporal annotations;
- polarity/negation;
- quantification where explicitly present;
- constraints;
- provenance;
- confidence;
- unresolved alternatives.

The IR must not require a globally known ontology.

A relation may therefore be represented as an anonymous operator:

```text
OperatorSymbol(id="op:7", arity=2)
```

with properties stored separately as hypotheses:

```text
symmetry = UNKNOWN
transitivity = UNKNOWN
inverse = UNKNOWN
composition = UNKNOWN
```

Names such as `located_in`, `owner`, `parent_of`, or benchmark-native relation labels are not required for execution.

### 5.1 Semantic identity

Each semantic object has a stable local identifier independent of its surface name.

For example, three sentences that express the same transfer event must converge on equivalent structures despite active/passive voice, mention order, synonym choice or language.

### 5.2 Surface quarantine

Reasoning contracts must not contain raw fields such as:

- `prompt`;
- `text`;
- `text_ru`;
- `renderer_id`;
- `split_id`;
- lexical template IDs;
- benchmark track names;
- gold relation names.

A debug-only provenance pointer may reference source turn/document IDs, but not expose raw strings to the executor.

## 6. Role and Entity Binder

Role binding is independent from surface grammar.

The binder converts mentions into semantic participants such as:

- AGENT;
- PATIENT;
- SOURCE;
- TARGET;
- OWNER;
- CONTENT;
- INSTRUMENT;
- LOCATION;
- TEMPORAL_ANCHOR;
- unresolved role variable.

These are general semantic roles, not benchmark answer labels.

The binder must preserve competing analyses when ambiguity is real. It must not collapse uncertainty solely to force an answer.

Core invariant:

```text
active(sentence) ~= passive(sentence) ~= reordered(sentence)
```

when all three are semantically equivalent.

## 7. Semantic World Inducer

The world inducer consumes Semantic IR and creates one or more candidate world models.

A world hypothesis contains:

- entity state;
- event state;
- relations/operators;
- constraints;
- temporal facts;
- provenance ledger;
- contradictions;
- unresolved variables;
- hypothesis score/confidence.

The world layer must support multiple simultaneous hypotheses rather than prematurely collapsing to one interpretation.

A minimal interface conceptually resembles:

```python
WorldSet = tuple[WorldHypothesis, ...]
```

where normalization ensures equivalent surface forms can be compared structurally.

### 7.1 No text in world execution

A `WorldHypothesis` contains no original prompt text. It contains only typed semantics and provenance references.

### 7.2 Revision

New observations may:

- add facts;
- supersede facts;
- retract facts;
- create conflicts;
- split a world hypothesis;
- eliminate a hypothesis.

This supports both long-horizon reasoning and uncertainty without treating memory as an unordered bag of statements.

## 8. Latent Rule Compiler

The latent rule compiler infers behavior of unknown operators from demonstrations and constraints.

The key requirement is that the compiler reasons over operator variables rather than hard-coded relation names.

Example induced form:

```text
OP(x, y) AND OP(y, z) -> OP(x, z)
```

The system may represent candidate properties such as:

- symmetry;
- asymmetry;
- transitivity;
- anti-transitivity;
- inverse mapping;
- composition;
- conditional activation;
- inhibitor/blocker;
- exception;
- temporal replacement;
- n-ary projection.

These are hypothesis families, not gold labels supplied by the task.

### 8.1 Rule induction discipline

Each rule hypothesis must track:

- observations explained;
- observations contradicted;
- minimum description complexity or comparable simplicity prior;
- confidence;
- provenance;
- competing alternatives.

The compiler should prefer the simplest rule family consistent with observations while retaining alternatives when evidence is insufficient.

### 8.2 No relation-name shortcut

A test must demonstrate that renaming an operator to a nonce token preserves inferred behavior.

The same test family must also include changed behavior under the same surface style so that the system cannot infer semantics from renderer structure alone.

## 9. Task Schema Inducer

World understanding and task understanding are separate problems.

The Task Schema Inducer infers what computation or output transformation is required from instructions and/or demonstrations.

P0 must support a compact task-program IR capable of representing at least:

- boolean/epistemic query;
- entity selection;
- ordered tuple extraction;
- set extraction;
- relation query;
- proof-path request;
- minimal sufficient explanation;
- abstention when no licensed answer exists.

The resulting `TaskProgram` is executable and independent of benchmark track names.

The executor must not receive phrases such as `classification`, `shortest proof`, `NOTA`, or other task-family hints unless those semantics were explicitly induced into the task program.

## 10. Compositional Executor

The executor is the deterministic or bounded-search reasoning core.

Inputs:

```text
WorldHypothesis
RuleProgram
TaskProgram
```

Output:

```text
ExecutionResult
```

The executor does not receive raw language.

Every derived fact must carry a derivation ledger containing the semantic facts and rule IDs used to derive it.

The initial executor should favor transparency and correctness over breadth.

P0 execution primitives should include:

- direct fact lookup;
- rule application;
- 2-5 step composition;
- inverse lookup where induced;
- blocked rule detection;
- contradiction propagation;
- unresolved result;
- finite bounded search to avoid runaway recursion.

## 11. Epistemic Controller

The epistemic layer owns answer status.

Required states:

```text
PROVED
DISPROVED
UNRESOLVED
CONFLICTED
```

The controller distinguishes:

- lack of evidence from negative evidence;
- supporting evidence from duplicated/copied support;
- contradiction from uncertainty;
- actual-world facts from counterfactual facts;
- sufficient evidence from merely suggestive evidence.

No other module may silently convert `UNRESOLVED` into a confident factual answer.

The epistemic result carries:

- state;
- answer payload if licensed;
- supporting derivations;
- contradicting derivations;
- confidence;
- abstention reason if applicable;
- provenance references.

## 12. Temporal State Machine

Long-horizon state is revision-aware.

Every mutable proposition can carry lifecycle state:

```text
ACTIVE
SUPERSEDED
RETRACTED
TEMPORARY
CONDITIONAL
```

A newer correction can supersede an older fact without deleting historical provenance.

Queries that ask for the current world use the active state. Queries about history may access superseded states explicitly.

P0 may implement only the state contract and minimal revision mechanics; full 100-turn optimization is later work.

## 13. Counterfactual Engine

Counterfactual reasoning clones a world hypothesis and applies an explicit intervention.

The actual world remains immutable.

Conceptually:

```text
ActualWorld
    + Intervention
    -> CounterfactualWorld
    -> Re-execution
```

The engine must be able to compare actual and counterfactual conclusions without contaminating the actual state.

This enables later support for necessary/sufficient causes, blockers and inhibitors.

## 14. Cross-Lingual Semantic Bridge

Language belongs to the surface layer.

Russian is the primary conversational surface, while English and bounded Kazakh transfer map into the same Semantic IR.

The target invariant is semantic equivalence rather than identical tokenization:

```text
Sem(RU(x)) ~= Sem(EN(x)) ~= Sem(KZ(x))
```

Cross-language reasoning does not get separate logic engines.

The initial P0 may use deterministic fixtures and controlled parsers to prove the architecture before neural multilingual encoders are connected.

## 15. Generalization Governor

The Generalization Governor measures stability of a candidate solution under semantics-preserving transformations.

It operates on semantic perturbation contracts, not hidden benchmark metadata.

Applicable checks include:

- paraphrase invariance;
- active/passive invariance;
- mention-order invariance;
- entity rename invariance;
- nonce operator rename invariance;
- cross-language equivalence;
- irrelevant distractor robustness;
- answer change under true semantic intervention.

A transformation marked semantics-preserving should not change the latent answer. A semantic intervention expected to change the world should change the result when logically relevant.

Instability lowers `generalization_confidence` and can trigger evaluation of an alternate world/rule hypothesis.

The governor must never use FTX1 BLIND renderer IDs, pair IDs, gold labels or split metadata.

## 16. Russian Surface Renderer

The renderer converts an epistemically licensed semantic result into natural Russian.

It has no authority to invent claims.

The renderer receives a structured result rather than the original reasoning prompt.

If the epistemic result is unresolved or conflicted, the renderer must faithfully express that state instead of forcing a direct answer.

Existing v2 Russian surface logic may be adapted as a donor, but only behind a v3 output contract.

## 17. Unified v3 runtime

The runtime orchestrates the complete path and records trace events.

Conceptual API:

```python
class UnifiedNexusV3P0:
    def respond(self, request: SurfaceRequest) -> V3Response:
        observations = self.surface.parse(request)
        bound = self.binder.bind(observations)
        worlds = self.world_inducer.update(bound)
        rules = self.rule_compiler.induce(worlds, request.demonstrations)
        task = self.task_inducer.induce(request.task_examples)
        candidates = self.executor.execute(worlds, rules, task)
        epistemic = self.epistemic.resolve(candidates)
        audited = self.generalization.audit(...)
        return self.renderer.render(audited)
```

This is an architectural sketch, not a mandated exact signature. Final signatures are defined during implementation planning and TDD.

## 18. Authority model

v3 keeps the strongest concept from v2: proposal is separate from committed truth.

No parser, rule inducer, task inducer or donor adapter has independent factual commit authority.

A result can become an asserted answer only after:

1. derivation is valid under the selected world/rule/task program;
2. epistemic state licenses assertion;
3. generalization checks do not expose a material invariance failure;
4. renderer faithfully preserves the structured answer.

This keeps semantic reasoning, evidential authority and surface generation separate.

## 19. v2 donor policy

Unified v2 is immutable.

A v3 adapter may call a v2 component only if:

- input/output is converted through a typed adapter;
- raw v2 task-family labels do not enter v3 reasoning state;
- the donor is replaceable without changing v3 public contracts;
- an ablation test can disable the donor;
- v3 can distinguish donor suggestion from authoritative result.

Donors are accelerators, not architectural authorities.

## 20. Anti-shortcut rules

The following are forbidden in P0 reasoning code:

- branching on benchmark split/track name;
- branching on case ID pattern;
- known FTX1 renderer fingerprints;
- relation-name lookup tables tailored to benchmark relations;
- answer-position priors;
- hidden gold-adjacent metadata;
- regexes that directly map known benchmark wording to answers;
- reading BLIND corpus or BLIND gold before preblind freeze;
- post-BLIND tuning on FTX1.

Regex and deterministic parsing are permitted only as generic surface extraction mechanisms when tests prove semantics survive lexical/operator renaming and paraphrase changes.

## 21. Development and evaluation discipline

### 21.1 DEV

DEV is visible and may be used for unit tests, debugging and architecture development.

### 21.2 Synthetic meta-training universes

Generalization training, if/when neural components are added, uses synthetic or independent meta-training universes that vary:

- ontology symbols;
- operator names;
- relation algebra;
- surface forms;
- languages;
- task schemas;
- entity names;
- distractors;
- causal structure.

The objective is transfer across sampled universes, not memorization of one benchmark family.

### 21.3 SHADOW

SHADOW is an audit distribution. It is not treated as a conventional training set and is not repeatedly optimized against failure-by-failure.

### 21.4 PREBLIND freeze

Before any BLIND evaluation, freeze:

- source commit SHA;
- dependency lock/hash;
- runtime config hash;
- model/artifact hashes;
- DEV/SHADOW result report;
- ablation report;
- generalization invariance report.

### 21.5 BLIND

FTX1 BLIND is one-shot.

If the preblind system fails the promotion gate after BLIND inspection, that version is not tuned against the inspected BLIND corpus. A future scientific attempt requires a fresh sealed benchmark family.

## 22. P0 success criteria

P0 is considered architecturally successful only if all of the following are demonstrated by automated tests:

1. at least three materially different surface forms of the same fact normalize to equivalent semantic/world representations;
2. active/passive role swaps preserve semantic roles;
3. entity renaming does not change the induced rule;
4. nonce operator renaming does not change the induced rule;
5. a previously unseen transitive-like operator can be induced from demonstrations without a predefined relation name;
6. at least one non-transitive or blocked operator family is distinguished from the transitive hypothesis;
7. a task program is induced from demonstrations rather than selected from a benchmark track ID;
8. 2-5 step compositional execution produces a provenance ledger;
9. `UNRESOLVED` and `CONFLICTED` are preserved through rendering;
10. downstream executor tests prove no raw text field is accepted by its public contract;
11. semantics-preserving transformations keep the result stable;
12. a real semantic intervention changes the result where expected.

These are architecture gates, not the final FTX1 promotion metrics.

## 23. Failure behavior

Fail closed whenever semantic or epistemic uncertainty is material.

Examples:

- ambiguous binding with no dominant hypothesis -> `UNRESOLVED`;
- equally supported contradictory worlds -> `CONFLICTED`;
- rule induction underdetermined -> preserve competing rules or abstain;
- executor search limit reached -> unresolved with trace reason;
- renderer/semantic guard mismatch -> reject surface answer;
- generalization invariance violation -> lower confidence and evaluate alternate hypothesis; if unresolved, abstain.

Silent guessing is treated as an error, not a feature.

## 24. Observability and traces

Every v3 response records structured trace events for:

- surface parsing;
- binding;
- world creation/revision;
- rule hypotheses created/eliminated;
- task program induction;
- rule applications;
- epistemic decision;
- generalization audit;
- rendering/guard outcome.

Trace data must avoid exposing sealed benchmark gold metadata.

The trace exists for engineering diagnosis and ablations, not as a runtime shortcut channel.

## 25. Testing strategy

Implementation follows TDD.

The order is behavior-first:

1. semantic contracts and surface quarantine;
2. semantic equivalence normalization;
3. role/entity binding;
4. world hypothesis construction;
5. unknown-rule induction;
6. task-program induction;
7. compositional executor;
8. epistemic states;
9. generalization invariance;
10. minimal Russian rendering;
11. P0 vertical runtime.

Each capability starts with a failing test.

Tests must include negative controls so that a mechanism cannot pass merely by always producing the same normalized structure or always assuming transitivity.

## 26. Ablation requirements

The P0 runtime must support targeted ablations for at least:

- rule inducer;
- task inducer;
- generalization governor;
- donor adapters;
- epistemic controller.

Ablations are required to determine whether observed gains come from the intended mechanism or from an unrelated fallback.

## 27. Scale-up path after P0

Only after P0 proves the architecture do we add learned components.

The intended progression is:

```text
P0: symbolic/typed proof of architecture
P1: learned semantic parser + latent representation alignment
P2: learned/meta-learned rule induction over synthetic universes
P3: multilingual semantic bridge + long-horizon state learner
P4: neural-symbolic hypothesis search and generalization governor
P5: full conversational integration and preblind freeze candidate
```

Each stage must preserve the same public semantic contracts so components can be replaced without collapsing the architecture.

## 28. Training objective direction

When neural training begins, the optimization target must include transfer behavior rather than only in-distribution task accuracy.

Candidate objective components include:

- task correctness;
- semantic contrastive alignment across paraphrases;
- role invariance;
- cross-language semantic alignment;
- operator/entity rename invariance;
- intervention sensitivity;
- OOD retention;
- calibration/abstention quality;
- penalty for surface-feature dependence;
- rehearsal/regression preservation.

A useful high-level objective is to maximize performance while minimizing generalization gap across sampled universes.

No exact loss weighting is frozen in this architecture spec; that belongs to a later training-design specification after P0 establishes the interfaces.

## 29. Security of the scientific result

The benchmark itself is treated like a sealed measurement instrument.

The design explicitly separates:

```text
system development
from
blind measurement
```

This is necessary because once a BLIND corpus is inspected, it is no longer a clean measure of far transfer for future tuning.

The v3 branch must therefore never contain the sealed FTX1 BLIND generator or gold corpus before one-shot evaluation.

## 30. Definition of done for this design

The design is ready for implementation planning when:

- all component boundaries above are explicit;
- raw-text quarantine is a hard interface requirement;
- v2 immutability is preserved;
- P0 success tests are falsifiable;
- anti-shortcut constraints are explicit;
- preblind discipline is explicit;
- no BLIND-dependent requirement is introduced;
- no implementation step requires access to sealed BLIND content.

The next artifact after approval of this written spec is a detailed implementation plan created before production code is written.
