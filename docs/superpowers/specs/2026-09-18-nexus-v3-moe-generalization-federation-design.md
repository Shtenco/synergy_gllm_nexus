# NEXUS Unified v3-MoE Generalization Federation — Design

**Status:** APPROVED ARCHITECTURE / PRE-IMPLEMENTATION  
**Date:** 2026-09-18  
**Branch:** `unified-v3-generalization-first`  
**Parent checkpoint:** `183c2fea809d724c9d3f5290f6c06985958f10a0`  
**Name:** `NEXUS Unified v3-MoE Generalization Federation`  
**Short name:** `NEXUS v3-MoE GF`

## 1. Objective

Build a hierarchical Mixture-of-Experts NEXUS that preserves the strongest verified capabilities of historical NEXUS generations while keeping Unified v3 as the sovereign reasoning and verification core.

The MoE MUST NOT average incompatible model weights and MUST NOT use majority vote as final authority.

Each expert emits typed proposals only. Final authority remains with:

```text
Semantic IR
-> World/Hypothesis Model
-> Rule/Task Programs
-> Executor
-> Evidence/Conflict Controller
-> Counterfactual Engine
-> Generalization Governor
-> Epistemic Consensus
-> Final Renderer
```

Core principle:

```text
TEXT IS NOT THE WORLD
EXPERT OUTPUT IS NOT THE TRUTH
VERIFIED WORLD STATE IS AUTHORITY
```

## 2. Why MoE instead of one merged model

Historical NEXUS generations are heterogeneous specialists.

Examples:

- R7-L D192: fast induction of unseen operators from support demonstrations.
- R7.2: Russian language bridge for unseen structured operators.
- R7.6: semantic/paraphrase transfer.
- R7.8/R7.10: formal/proof-first reasoning.
- R7.14: Russian morphology/canonicalization.
- R7.18: evidence policy, revision, probability, multilingual/causal reasoning.
- R7.44.3: persistent context/discourse state.
- V10 600K InfoGraph: procedural unseen transfer.
- Ω-1.5R2: relation/role/argument graph construction.
- Unified R1.3: broad compound/open-set fallback.
- v3 P0.1: competing world hypotheses, rule algebra, temporal revision, counterfactuals, epistemic consensus.

These systems differ in architecture, training targets, interfaces, and evidence quality. Weight averaging would destroy specialist structure. Majority vote would give equal influence to experts outside their competence.

The correct abstraction is a capability federation.

## 3. Expert roster

### 3.1 Primary active experts

| Expert | Primary capability | Authority boundary |
|---|---|---|
| `r7l_fast_induction` | few-shot unseen-operator induction | proposes latent operator/rule programs only |
| `r72_language` | Russian unseen-operator semantic binding | proposes normalized semantics/operator bindings |
| `r76_semantic_memory` | paraphrase/semantic-memory transfer | proposes semantic matches/support |
| `r78_formal` | formal proof/architecture-stress reasoning | proposes proof candidates |
| `r710_proof` | proof-first multi-domain reasoning | proposes proof/evidence chains |
| `r714_morpholex` | morphology/canonicalization | non-authoritative normalization only |
| `r718_evidence` | evidence trust/revision/probability/multilingual | proposes evidence-weighted claims |
| `r744_context` | dialogue/context/revision state | proposes context/world updates |
| `omega15r2_graph` | relation roles/subject/object/triple construction | proposes graph facts |
| `v10_procedural` | procedural unseen-transfer | proposes procedural hypotheses |
| `unified_r13` | broad compound/open-set support | fallback proposal expert |
| `v3_hypothesis` | world/rule/task hypothesis search | native sovereign proposal/search expert |

### 3.2 Shadow-only experts

`v30_procedural` is initially shadow-only.

It may produce telemetry/proposals but cannot affect final answers until calibration proves positive marginal utility. The reason is its strong procedural unseen score combined with historically weak natural dialogue.

Other archived versions may be added later only through the Expert Registry and must start in shadow mode.

## 4. Expert contract

All experts implement the same typed interface.

```python
ExpertProposal(
    proposal_id,
    expert_id,
    capability,
    semantic_facts,
    world_hypotheses,
    rule_hypotheses,
    task_hypotheses,
    answer_candidates,
    proof_steps,
    evidence_items,
    confidence,
    uncertainty,
    provenance,
    compute_cost,
    latency_ms,
    failure_flags,
)
```

### 4.1 Mandatory properties

An expert:

- cannot write directly to final answer;
- cannot directly commit world state;
- cannot bypass the epistemic controller;
- cannot inspect benchmark split/track/gold metadata;
- must attach provenance;
- must report uncertainty;
- may abstain;
- may fail closed.

### 4.2 Proposal normalization

Every proposal is normalized into v3 contracts before fusion.

Raw expert-specific outputs are not consumed by the final executor.

## 5. MoE architecture

```text
USER / DIALOGUE / SUPPORT DEMOS
            |
            v
+-----------------------------+
| Surface + Context Front End |
+-----------------------------+
   |          |          |
   v          v          v
 R7.2       R7.14      R7.44.3
 Binder    MorphoLex    Context
   \          |          /
    +---------+---------+
              |
              v
         Semantic IR
              |
              v
+-----------------------------+
|  Capability / Novelty Gate  |
+-----------------------------+
              |
              v
+-----------------------------+
| Learned Cognitive Top-K MoE |
+-----------------------------+
   |   |   |   |   |   |   |
   v   v   v   v   v   v   v
 R7L V10 R78 R710 R718 Ω15R2 UnifiedR13 ...
   \   |   |   |   |   |   /
    +--+---+---+---+---+---+
              |
              v
      ExpertProposal Set
              |
              v
+-----------------------------+
| Proposal Fusion / Calibration|
+-----------------------------+
              |
              v
      v3 Hypothesis Beam
              |
              v
         Rule AST / Task IR
              |
              v
        World Simulation
              |
              v
 Evidence + Conflict Analysis
              |
              v
      Counterfactual Checks
              |
              v
    Generalization Governor
              |
              v
     Epistemic Consensus
              |
              v
          Final Answer
```

## 6. Surface and context stage

The front end is not itself a final router.

Its job is to create a robust typed observation layer.

### 6.1 R7.2

R7.2 is invoked when support demonstrations or latent operator semantics are present.

It proposes:

- operator binding;
- instruction/content disentanglement;
- normalized entity/relation arguments.

### 6.2 R7.14

R7.14/MorphoLex provides:

- morphology normalization;
- lexical canonicalization;
- variant/surface stabilization.

It NEVER receives answer authority.

### 6.3 R7.44.3

Context expert proposes:

- coreference bindings;
- active/superseded dialogue state;
- revision events;
- persistent context facts.

Context updates remain proposals until accepted by the v3 world model.

## 7. Capability Router

Introduce `CapabilityRouter`.

Input is typed semantic/task/world context, not raw benchmark labels.

Features may include:

- language;
- task-program distribution;
- presence/count of support demonstrations;
- entity count;
- operator novelty;
- relation novelty;
- graph density;
- temporal markers;
- causal markers;
- evidence/conflict indicators;
- dialogue-state depth;
- memory requirement;
- proof request;
- counterfactual requirement;
- uncertainty;
- hypothesis entropy;
- estimated compute cost.

Forbidden router features:

- benchmark name;
- track ID;
- split ID;
- case ID pattern;
- gold answer;
- gold rule;
- renderer/template ID.

Output:

```text
P(expert | semantic state)
```

Default active `Top-K = 2..4`.

The router may select fewer experts when confidence is high and more when novelty/disagreement is high.

## 8. Novelty Gate

A separate `NoveltyGate` prevents forced routing to familiar experts.

Inputs:

- router entropy;
- maximum calibrated expert confidence;
- semantic distance;
- rule-AST novelty;
- expert disagreement;
- OOD detector score;
- support-demonstration availability.

States:

```text
KNOWN
UNCERTAIN
NOVEL
```

### 8.1 NOVEL path

When `NOVEL`:

```text
Support demonstrations
        ->
R7-L Fast Induction
        +
v3 Rule/World Hypothesis Search
        ->
candidate latent rules
        ->
prediction
        ->
evidence comparison
        ->
revision
```

The system does not map a novel rule to the nearest historical capability merely to obtain an answer.

## 9. R7-L Fast Induction donor

R7-L is a first-class cognitive donor rather than a benchmark artifact.

The original cognitive primitive is:

```text
support examples S
-> encoded immutable fast memory
-> query representation H
-> recurrent attention over S
-> latent operator response
```

For v3-MoE the first implementation preserves the frozen R7-L behavior through an adapter.

Later training generalizes this primitive from fixed permutation operators to typed rule-program proposals.

R7-L output must become a `RuleHypothesis`/`ExpertProposal`, never a final answer.

## 10. v3 Hypothesis expert

The existing P0.1 v3 subsystem remains the integration authority for novel reasoning.

Responsibilities:

- competing world hypotheses;
- candidate rule programs;
- candidate task programs;
- bounded beam search;
- prediction ledger;
- temporal revision;
- conflict preservation;
- counterfactual worlds;
- epistemic consensus.

The historical experts enlarge the proposal space; they do not replace this core.

## 11. Proposal Fusion

No majority voting.

Introduce `ProposalFusion`.

Each proposal receives calibrated utility terms:

```text
utility =
    task_fit
  + verified_support
  + independent_evidence
  + predictive_consistency
  + generalization_stability
  + historical_calibration
  - contradictions
  - unsupported_claims
  - OOD_penalty
  - latency_cost
  - compute_cost
```

The fusion layer outputs:

- accepted facts;
- competing facts;
- candidate rules;
- candidate tasks;
- conflict sets;
- proposal provenance graph.

Independent agreement is stronger than duplicated/correlated evidence.

## 12. Expert correlation control

Historical experts often share lineage.

The system therefore stores `lineage_group`.

Examples:

- R7-L/R7.2 are related.
- R7.8/R7.10/R7.18 share later R7 lineage.
- Ω-1.4/1.5/1.5R2 are related.
- Unified systems inherit several donors.

Multiple experts from one lineage do not count as fully independent evidence.

Epistemic consensus uses effective independent support, not raw expert count.

## 13. Calibration

Every expert has a capability-conditioned calibrator.

Calibration keys may include:

- capability;
- language;
- support/no-support mode;
- proof depth;
- novelty bucket;
- domain family.

The calibrator learns:

```text
P(proposal correct | expert, context)
```

Calibration may decrease expert confidence but cannot increase it beyond explicit configured caps until enough held-out calibration evidence exists.

## 14. Failure semantics

### Expert load failure

- hash mismatch -> disable expert;
- missing artifact -> disable expert;
- incompatible runtime -> disable expert;
- timeout -> failed proposal;
- malformed schema -> reject proposal;
- exception -> trace + abstain.

No fallback silently impersonates another expert.

### Router failure

If router is uncertain:

- widen Top-K;
- include v3 native hypothesis expert;
- lower final confidence.

### Disagreement

If experts conflict materially:

```text
CONFLICT
-> provenance comparison
-> evidence independence
-> world simulation
-> counterfactual check
-> generalization audit
-> PROVED / DISPROVED / CONFLICTED / UNRESOLVED
```

## 15. Training strategy

### 15.1 Freeze experts first

Initial MoE training freezes all historical expert checkpoints/logic.

Train only:

- capability router;
- novelty gate;
- expert calibrators;
- proposal fusion;
- MoE epistemic weighting.

This protects historical capabilities.

### 15.2 Router targets

Router supervision is utility-based, not benchmark-label-based.

For each episode, execute available experts offline and estimate marginal contribution.

Example:

```text
R7-L   correct, strong support
R7.10  wrong
R7.18  abstain
v3     correct
```

The router target promotes R7-L and v3 while suppressing R7.10.

### 15.3 Counterfactual router supervision

Training includes expert-removal ablations.

If removing expert X changes a correct fused result to wrong/unresolved, X has positive marginal utility.

If adding X changes a correct result to wrong/conflicted without useful evidence, X receives negative utility.

### 15.4 Cost-aware routing

Training objective includes compute.

```text
router_reward =
    verified_correctness
  + robustness
  + calibration
  - expert_count_cost
  - latency
  - redundant_lineage_cost
```

The router learns not to invoke all experts by default.

## 16. MoE training curriculum

Curriculum contains independent families for:

- T1 surface/paraphrase transfer;
- T2 unseen operator + support demonstrations;
- T3 Russian unseen operator;
- T4 semantic/structural OOD;
- T5 new rule-AST language;
- context revisions;
- evidence conflicts;
- temporal state;
- causal composition;
- counterfactuals;
- open-set/NOTA;
- multilingual transfer;
- long-horizon reasoning.

HARD-OOS D is already consumed. It may inform training-family design but can no longer serve as a clean OOS benchmark.

FTX1 BLIND remains sealed and is NOT used for training, calibration, router selection, thresholds, or ablations.

## 17. Distillation phase — deferred

After the frozen-expert MoE proves useful, a later optional phase may distill verified expert trajectories into a unified student cortex.

This phase is explicitly out of scope for first v3-MoE implementation.

The initial objective is federation, not compression.

## 18. Benchmark strategy

### 18.1 Regression suite

Preserve:

- all existing Unified v3 P0/P0.1 tests;
- R7-L donor reproduction;
- R7.2 operator-transfer reproduction;
- v2 donor contract tests where used;
- historical artifact hash checks.

### 18.2 New FAST-TRANSFER F1

Purpose:

```text
new operator families
+
support demonstrations
+
surface/language changes
```

Metrics:

- induction accuracy;
- operator-all-queries;
- worst-family accuracy;
- adaptation examples required;
- no-weight-update compliance;
- support efficiency;
- RU/EN/KZ retention.

### 18.3 New HARD-OOS F

Purpose:

```text
new AST grammar
+
new rule topology
+
new world binding
+
temporal/inhibitor/counterfactual structures
```

It is authored independently after MoE training is frozen.

HARD-OOS D is not reused as OOS.

### 18.4 FTX1

FTX1 remains the highest-value sealed end-to-end benchmark.

It is opened only under the existing one-shot protocol after preblind source/weights/config freeze.

## 19. Success metrics

The MoE is not accepted merely because aggregate accuracy rises.

Required measurements:

- router top-1/top-k recall of useful experts;
- oracle expert ceiling;
- fused answer accuracy;
- best-single-expert accuracy;
- MoE gain over best single expert;
- negative-transfer rate;
- expert abstention accuracy;
- calibration ECE/Brier;
- average experts/query;
- p50/p95 latency;
- lineage-adjusted evidence gain;
- novelty detection AUROC;
- unseen-operator transfer;
- AST structural transfer;
- counterfactual correctness;
- generalization gap.

Critical new metric:

```text
Negative Transfer Rate =
cases where MoE converts a correct best-expert trajectory
into a wrong final result
/
cases with at least one correct expert
```

This must remain very low.

## 20. Initial promotion gates

Development gates for v3-MoE:

```text
MoE >= best single expert + 5 pp on mixed META-OOS
Negative Transfer Rate <= 2%
Router useful-expert Top-K recall >= 95%
Expert schema failures = 0 accepted
Hash-mismatch experts = 0 loaded
Rename invariance >= 95%
Novelty OOD AUROC >= 0.90
Expected-change intervention sensitivity >= 90%
Calibration ECE <= 0.10
```

FAST-TRANSFER F1 and HARD-OOS F receive independent preregistered gates before opening.

These do not replace FTX1 promotion gates.

## 21. Repository layout

```text
src/nexus_gllm/unified_v3/moe/
    __init__.py
    contracts.py
    registry.py
    lineage.py
    capability_router.py
    novelty_gate.py
    calibration.py
    proposal_fusion.py
    runtime.py

    experts/
        base.py
        r7l_fast_induction.py
        r72_language.py
        r76_semantic_memory.py
        r78_formal.py
        r710_proof.py
        r714_morpholex.py
        r718_evidence.py
        r744_context.py
        omega15r2_graph.py
        v10_procedural.py
        unified_r13.py
        v3_hypothesis.py
        v30_shadow.py

training/v3_moe/
    episode.py
    expert_rollout.py
    utility.py
    dataset.py
    router_model.py
    novelty_model.py
    calibration.py
    train_router.py
    evaluate.py

tests/unified_v3_moe/
    test_contracts.py
    test_registry_hashes.py
    test_router.py
    test_novelty_gate.py
    test_lineage_independence.py
    test_proposal_fusion.py
    test_expert_fail_closed.py
    test_r7l_adapter.py
    test_r72_adapter.py
    test_context_adapter.py
    test_evidence_adapter.py
    test_moe_runtime.py
    test_negative_transfer.py

tests/v3_moe_training/
    test_feature_quarantine.py
    test_utility_targets.py
    test_router_smoke.py
    test_novelty_smoke.py
    test_calibration.py
    test_meta_oos.py
```

## 22. Expert Registry

Every expert entry stores:

```python
ExpertSpec(
    expert_id,
    version,
    capability_tags,
    lineage_group,
    artifact_path,
    artifact_sha256,
    adapter_class,
    active_mode,
    max_latency_ms,
    confidence_cap,
)
```

`active_mode`:

```text
ACTIVE
SHADOW
DISABLED
```

No expert enters ACTIVE mode without:

- artifact/hash verification;
- adapter tests;
- capability regression test;
- calibration record.

## 23. Historical artifact policy

Where exact historical checkpoint/runtime is available, use it.

Where only an already faithful donor adapter exists in Unified v2, the first MoE iteration may wrap that donor adapter but MUST mark provenance as `ADAPTER_RECONSTRUCTION`, not `EXACT_HISTORICAL`.

The system never claims exact restoration where only reconstructed logic exists.

## 24. Authority boundaries

Only these components may alter sovereign state:

1. v3 world/hypothesis engine through typed commit rules;
2. evidence/conflict controller through validated provenance;
3. temporal/counterfactual engine through typed state transitions;
4. epistemic controller for final status.

Historical experts cannot:

- write final answer;
- mutate world directly;
- overwrite contradictions;
- suppress counterevidence;
- mark their own claims proved.

## 25. First implementation milestone — MoE P0

The first vertical slice does NOT require all experts.

Activate first:

```text
R7-L
R7.2
R7.18
R7.44 context donor
Ω-1.5R2 / graph donor
v3 hypothesis expert
```

Keep:

```text
R7.6
R7.8
R7.10
R7.14
V10
Unified R1.3
V30
```

in registry/shadow integration until adapters and artifacts are verified.

The P0 success episode must demonstrate:

1. support demonstrations trigger R7-L;
2. Russian formulation activates R7.2;
3. context revision invokes context expert;
4. evidence conflict invokes R7.18;
5. graph/role ambiguity invokes graph expert;
6. router selects Top-K rather than all experts;
7. proposals normalize to one contract;
8. conflict does not become majority vote;
9. v3 hypothesis engine commits final world;
10. removing the useful expert degrades result;
11. adding an irrelevant expert does not change the result;
12. novelty gate can widen routing or abstain.

## 26. Training milestone — Router P1

After MoE P0 contracts are green:

- generate/assemble mixed expert-rollout corpus;
- freeze train/dev/OOS families;
- run all active experts offline;
- compute marginal utility;
- train router;
- train novelty detector;
- calibrate expert probabilities;
- evaluate against:
  - best single expert;
  - always-all-experts;
  - random Top-K;
  - heuristic router;
  - oracle router.

No FTX1 BLIND is used.

## 27. Definition of done

NEXUS v3-MoE GF is not complete when routing code exists.

It is complete for first promotion only when:

```text
historical capability experts
-> typed proposal federation
-> learned cost-aware Top-K routing
-> novelty-aware fast induction
-> lineage-aware fusion
-> v3 sovereign world verification
-> lower negative transfer than naive ensemble
-> measurable gain over best single expert
```

and these claims are supported by frozen hashes, regression tests, ablations, and a fresh OOS benchmark that was not used for training.
