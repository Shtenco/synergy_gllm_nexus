# NEXUS GLLM Ω-1.5 — Universal Graph Argument Cortex

**Date:** 2026-09-16  
**Status:** user-approved architectural direction; Blind-3 frozen before model code  
**Repository:** `Shtenco/synergy_gllm_nexus`  
**Runtime invariant:** no pretrained LLM/tokenizer is part of canonical Ω-1.5 inference or training.

## 1. Measured problem

Ω-1.4 substantially improved semantic relation transfer, but end-to-end exact graph construction is now limited by argument generalization rather than by the canonical relation organ.

Frozen Ω-1.4 Blind-2 evidence:

- Blind-2A relation accuracy: 76.60%;
- Blind-2A subject exact: 0.48%;
- Blind-2A object exact: 60.01%;
- Blind-2A strict non-abstain graph: 0%;
- Blind-2B relation accuracy: 50.00%;
- Blind-2B subject exact: 13.18%;
- Blind-2B object exact: 16.15%;
- Blind-2B strict non-abstain graph: 0%.

The candidate lattice was expressive enough for most Blind-2 cases, so the primary problem is **role-conditioned selection of the correct arguments**, especially SUBJECT, under long, reordered and distractor-rich Russian surface forms.

Ω-1.5 therefore changes the argument organ from independent span scoring into a **joint recurrent factor graph over typed candidate nodes, semantic operators and argument roles**.

## 2. Core thesis

The canonical triple is inferred jointly:

`SUBJECT -> OPERATOR -> OBJECT`

The model optimizes the structured posterior:

`P(s,o,r | x) ∝ P(r | x,s,o) * P(s | x,r) * P(o | x,r,s)`

In log-factor form:

`F(s,o,r) = R(r|x,s,o) + A_s(s|x,r) + A_o(o|x,r,s) + G(s,o,r)`

where:

- `R` is the Ω-1.4 semantic-operator score;
- `A_s` is relation-conditioned subject compatibility;
- `A_o` is relation-and-subject-conditioned object compatibility;
- `G` is a deterministic graph/operator compatibility factor.

The model is not a left-to-right text generator. Its central operation is recurrent structured inference over graph candidates.

## 3. Architectural alternatives considered

### A. Iterative factor-graph matching — selected

Candidates, role slots and canonical operators exchange messages for several iterations. Each component remains interpretable and independently testable.

Advantages:
- directly models the measured Ω-1.4 bottleneck;
- graph-native and compatible with NEXUS operator authority;
- supports joint relation/argument refinement;
- works with bounded Top-K candidate sets on CPU;
- preserves auditable factors and deterministic graph constraints.

### B. DETR-like set prediction with Hungarian matching — auxiliary only

Useful when one sentence contains multiple gold triples. It is not the primary Ω-1.5 inference mechanism because full set prediction would spend unnecessary capacity on permutation resolution before single-triple generalization is solved.

### C. Biaffine span-role pointers — rejected as primary

Fast, but it conditions role scoring only weakly on the evolving semantic operator state and risks recreating the Ω-1.3 failure mode: good local span scores without a truly joint semantic triple.

## 4. Pre-model-code Blind-3 freeze

The following manifest was committed before Ω-1.5 model code:

`benchmarks/frozen/OMEGA15_BLIND3_FREEZE_MANIFEST.json`

Frozen splits:

- Shadow-Dev-3: 12,000, SHA-256 `68aadb444aeb7c108733b55a3e1ae55ff5b53842070ad34c400107084f3cb1e4`;
- Blind-3A: 10,000, SHA-256 `9d642ad3ed11e9c7f858937c83396a21259a821847680a23977f16e77ab2049a`;
- Blind-3B: 2,000, SHA-256 `2b707b34a79247099a154d338d44db682c65bea2d895b1613966825240130ef3`;
- generator SHA-256 `7879d3762f6d93709056b25670cdcf1a647ef63282468d2edfd67d11e76a6ab4`.

Normalized surface overlap and template-hash overlap are zero between every pair of Shadow-Dev-3 / Blind-3A / Blind-3B.

Blind-3A/B are forbidden for:
- architecture selection;
- candidate-generator tuning;
- loss-weight tuning;
- threshold tuning;
- early stopping;
- checkpoint selection.

Only Shadow-Dev-3 and protected historical dev suites may influence those choices.

## 5. Blind-3 challenge families

Blind-3 contains balanced known relations plus NOTA and eight surface-transformation families:

1. plain unseen surface;
2. distractor prefix;
3. distractor suffix;
4. two relations in one sentence;
5. surface argument reversal;
6. pronoun/context distractor;
7. negated distractor;
8. event/context wrapper.

Gold arguments span 1–6 whitespace-delimited words. Blind-3B uses longer human-like clauses and narrative ordering that differs from semantic ordering.

## 6. Candidate Node Cortex

Ω-1.5 no longer assumes a 1–2-word candidate lattice.

For each text `x`, the candidate generator proposes at most `K=48` nodes from four proposal families:

- word spans of width 1–6;
- clause chunks split by punctuation / conjunction boundaries;
- event chunks containing temporal or causal operator evidence;
- context/antecedent chunks used as auxiliary candidates.

Every `CandidateNode` contains:

```text
CandidateNode {
  start_char,
  end_char,
  surface,
  width_words,
  clause_id,
  type_logits: ENTITY / EVENT / CONTEXT / NULL,
  boundary_score,
  local_ngram_state,
  morphology_state,
  position_state,
  operator_evidence_state
}
```

Candidate identity strings are never used as direct memorization features. Entity-specific information is masked or bottlenecked before semantic role scoring.

## 7. Candidate proposal and Top-K

A cheap boundary/type proposal stage scores all admissible word spans and clause/event chunks.

The Top-K selector keeps at most 48 candidates using a deterministic mixture of:

`proposal_score = boundary + type_confidence + operator_evidence + coverage_bonus`

Coverage bonus prevents all Top-K slots from collapsing into one clause.

Training includes an explicit candidate-recall objective. The promotion target is:

`candidate recall@48 >= 99%`

on Shadow-Dev-3 before Blind-3 is opened.

## 8. Typed role slots

The recurrent workspace has explicit latent role slots:

- `SUBJECT`;
- `OBJECT`;
- `EVENT`;
- `CONTEXT`;
- `RELATION`.

For Stage Ω-1.5, SUBJECT and OBJECT determine the canonical triple. EVENT and CONTEXT provide auxiliary evidence and become directly supervised where the synthetic record exposes event/context structure.

Role slots have no authority to create graph facts until ProposalValidator and OperatorCard constraints accept the final triple.

## 9. Relation-conditioned bipartite matching

Let `h_i` be candidate representation and `q_r`, `q_s`, `q_o` the current relation, subject and object states.

Subject score:

`A_s(i,r) = MLP_s([h_i, q_r, h_i ⊙ q_r, type_i])`

Object score:

`A_o(j,r,s) = MLP_o([h_j, q_r, q_s, h_j ⊙ q_r, pair(i,j)])`

Pair features include:

- relative order;
- span overlap;
- same/different clause;
- token/character distance;
- candidate types;
- operator role compatibility;
- event/entity compatibility.

For each relation, the system therefore scores a bipartite assignment between candidate nodes and semantic role slots rather than independently choosing two local spans.

## 10. Joint triple factor

For one target triple:

`F(i,j,r) = relation_score(r) + subject_score(i,r) + object_score(j,r,i) + graph_factor(i,j,r)`

`graph_factor` is deterministic and may include:

- reject `i == j` for asymmetric binary relations;
- reject overlapping candidates when the operator forbids self-reference;
- temporal/causal relations prefer EVENT-compatible candidates;
- ownership/location/taxonomy/comparison prefer ENTITY-compatible candidates;
- OperatorCard directionality and inverse normalization;
- before/causes cycle-risk penalty when graph context exists.

The factor does not invent truth. It constrains structurally impossible or implausible assignments.

## 11. Iterative recurrent refinement

Ω-1.5 performs `T=4` refinement rounds by default.

Relation update:

`q_r^(t+1) = GRU_r(q_r^t, [global_x, E_s^t, E_o^t, operator_evidence])`

Subject update:

`q_s^(t+1) = GRU_s(q_s^t, [E_s^t, q_r^(t+1), E_o^t])`

Object update:

`q_o^(t+1) = GRU_o(q_o^t, [E_o^t, q_r^(t+1), E_s^t])`

where `E_s` and `E_o` are soft expected candidate embeddings under the current role distributions.

After each round, the semantic relation distribution is recomputed using Ω-1.4 prototype/evidence features conditioned on the current candidate-role expectations.

Thus relation improves arguments and arguments improve relation.

## 12. Fixed-point stopping

Inference may stop before `T=4` if for two consecutive rounds:

- top relation is unchanged;
- top SUBJECT candidate is unchanged;
- top OBJECT candidate is unchanged;
- joint-triple probability change < `epsilon_p`;
- top-1/top-2 joint margin > `margin_stop`.

`epsilon_p` and `margin_stop` are tuned on Shadow-Dev-3 only.

The number of refinement rounds and convergence reason are stored in telemetry.

## 13. Multiple triples

For Stage Ω-1.5 the primary supervised target remains one canonical triple per benchmark row. A sentence may contain a second distractor relation.

The architecture nevertheless exposes `decode_set(M)` for future multi-triple output. When a training record explicitly contains multiple gold triples, matching uses Hungarian assignment over triple costs:

`cost = relation_cost + subject_span_cost + object_span_cost + graph_constraint_cost`.

Multi-triple output is not required to pass the initial Ω-1.5 promotion gate.

## 14. Entity-bias suppression

The role/semantic encoder must not solve the task by memorizing entity names.

Ω-1.5 uses:

- argument surface masking in relation-semantic features;
- entity-name randomization during training;
- candidate-context hashing that replaces candidate identity with `<CAND>`;
- optional variational/information-bottleneck regularization only if Shadow-Dev-3 demonstrates entity leakage after the simpler controls.

No pretrained entity embedding table is used.

## 15. Training data

The canonical first run uses 100,000 Stage-A training situations, transformed online into Ω-1.5 joint examples.

Training augmentation is allowed only from pre-Blind sources:

- Stage-A train;
- Ω-1.4 pre-code semantic train bank;
- legacy NEXUS morphology/operator lexicons that were inspected before Blind-3;
- deterministic argument-length, word-order, clause and distractor augmentations whose template families are disjoint from Blind-3.

Blind-3 text may not be used to create training augmentations after freeze.

## 16. Losses

The canonical objective is:

`L = λcand L_candidate + λtype L_type + λsub L_subject + λobj L_object + λrel L_relation + λtriple L_joint_triple + λcons L_consistency + λnull L_NOTA + λrep L_replay`

Definitions:

- `L_candidate`: gold argument appears in Top-K / boundary ranking loss;
- `L_type`: candidate node type classification;
- `L_subject`: relation-conditioned SUBJECT cross-entropy;
- `L_object`: relation/subject-conditioned OBJECT cross-entropy;
- `L_relation`: protected Ω-1.4 canonical-operator objective;
- `L_joint_triple`: structured cross-entropy over valid `(s,o,r)` triples;
- `L_consistency`: penalty for OperatorCard/type/graph violations;
- `L_NOTA`: open-set/no-triple calibration;
- `L_replay`: protected Ω-1.4 relation semantics and Ω-1.2 memory/reasoning rehearsal.

Loss weights are tuned on Stage-A dev + Shadow-Dev-3 only.

## 17. Sovereignty and anti-regression

Ω-1.4 remains the protected semantic operator organ.

A strong verified canonical relation cue cannot be overwritten by a weak argument-side residual without passing the semantic evidence gate.

Checkpoint promotion requires:

- no protected Ω-1.4 relation regression >1 percentage point on Stage-A dev;
- no protected Ω-1.2 graph/memory regression;
- invalid accepted graph mutation rate = 0%.

If joint training violates a protected gate, the argument cortex is trained with the semantic operator organ frozen or through bounded adapters only.

## 18. Evaluation metrics

Every evaluation reports:

- candidate recall@16/@32/@48;
- candidate type macro-F1;
- SUBJECT exact;
- OBJECT exact;
- both-arguments exact;
- relation accuracy with gold arguments;
- relation accuracy with predicted arguments;
- strict canonical triple exact;
- strict non-NOTA triple exact;
- NOTA precision/recall/F1;
- invalid accepted mutation rate;
- average refinement rounds;
- fixed-point convergence rate;
- protected-suite deltas.

A relation-only improvement is not sufficient for Ω-1.5 promotion.

## 19. Checkpoint selection

Selection uses only:

- Stage-A dev;
- Shadow-Dev-3;
- protected historical regression suites.

Primary selection score:

`score = strict_non_NOTA_triple_exact + 0.25 * relation_accuracy + 0.10 * candidate_recall@48`

subject to hard gates:

- candidate recall@48 >= 99%;
- invalid accepted mutation = 0%;
- Ω-1.4 protected relation regression <=1 pp;
- NOTA precision on Shadow-Dev-3 >=98%.

Blind-3A/B metrics are absent from training checkpoints.

## 20. One-shot Blind-3 promotion gate

After checkpoint freeze and SHA-256:

1. evaluate frozen Ω-1.4 baseline on Blind-3A/B;
2. evaluate Ω-1.5 exactly once on the same splits;
3. do not tune Ω-1.5 from those results.

Promotion to 250K requires all of:

- Ω-1.5 strict non-NOTA triple exact > Ω-1.4 baseline on the same Blind-3 corpus;
- candidate recall@48 >=99%;
- Ω-1.5 relation accuracy no worse than Ω-1.4 by more than 1 pp;
- NOTA precision >=98%;
- invalid accepted mutation rate =0%;
- protected Ω-1.2/Ω-1.4 regression gates pass.

Failure of any mandatory criterion blocks 250K scaling.

## 21. CPU execution contract

The canonical local environment remains CPU-only with limited RAM and long-process throttling.

Therefore:

- candidate representations are precomputed/cacheable where semantics are deterministic;
- Top-K is bounded at 48;
- joint factor computation is vectorized;
- canonical training is resumable in fresh processes while preserving model weights, optimizer moments, fixed permutation, cursor and best checkpoint;
- a completed 100K run means every training example was processed exactly according to the persisted permutation/cursor contract.

## 22. Files

Planned focused modules:

```text
src/nexus_gllm/
  candidate_nodes.py
  argument_factor_graph.py
  joint_graph_cortex.py
  joint_graph_schema.py

training/
  omega15_dataset.py
  train_omega15.py
  resume_omega15.py

benchmarks/
  run_omega15_benchmark.py

benchmarks/frozen/
  OMEGA15_BLIND3_FREEZE_MANIFEST.json

tests/
  test_omega15_candidates.py
  test_omega15_factor_graph.py
  test_omega15_training.py
  test_omega15_benchmark.py
```

Ω-1.4 `SemanticRelationCortex` and OperatorCards are reused, not duplicated.

## 23. Scientific boundary

Ω-1.5 is an internal graph-native Russian structured extraction experiment. Synthetic Blind-3 success would demonstrate transfer across specified relation/argument perturbations, not unrestricted Russian understanding or AGI. Claims must remain tied to measured frozen benchmarks and reproducible hashes.