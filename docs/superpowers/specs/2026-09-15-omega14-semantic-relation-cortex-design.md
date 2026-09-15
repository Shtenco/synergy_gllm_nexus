# NEXUS GLLM Ω-1.4 — Canonical Semantic Relation Cortex

**Date:** 2026-09-15  
**Status:** approved by user; Blind-2 frozen before model code  
**Runtime:** no pretrained LLM/tokenizer in canonical runtime

## 1. Measured problem
Ω-1.3 extracts arguments much better than it transfers relation semantics. Frozen Ω-1.3 Blind-1: relation 38.61%, subject exact 35.75%, object exact 78.95%, strict non-abstain graph 0.60%. Stage-A train contains only one normalized language surface for each non-abstain relation: `принадлежит`, `находится`, `является`, `старше`, `сначала…потом`, `поэтому`.

Therefore Ω-1.4 treats a relation as a **canonical operator**, not a flat label inferred directly from a surface phrase.

## 2. Legacy NEXUS mechanisms reused
- R7.2: CONTENT / INSTRUCTION disentanglement and hashed character n-gram language binding.
- R7.9: formal semantic IR and independent verifier; multi-trajectory is advisory, not authority.
- R7.12: residual correction over graph logits, gated so verified layers cannot be overwritten.
- R7.14: MorphoLex operator/morphology evidence as an additional feature state, not truth authority.
- R7.17: recurrent critic separated from sovereign answer truth.
- R7.18: candidate-specific evidence credit and fixed-point/margin stopping.
- R7.44.x: context inheritance requires explicit compatibility; lexical similarity alone is insufficient.
- NEXUS Ω supersystem: canonical operator `O`, contractive latent workspace `H`, learned != trusted.

## 3. Pre-code frozen evaluation
Committed manifest: `benchmarks/frozen/OMEGA14_BLIND2_FREEZE_MANIFEST.json`.
- Shadow-Dev-2: 12,000, SHA `8f290c239548b27582cd805a48f7ce14a583f10cc142e27a16318283426595c4`
- Blind-2A: 10,000, SHA `5330b1fb9c3b215aa70703381a78dd50d9b6d8fe05acc1c85716c7758ed5222b`
- Blind-2B: 2,000, SHA `2bbd717a2830ee32aff8cc283c428f7aa78d6fdb842363a1b0fbd59138365973`
- normalized-template overlap across train/shadow/blind pairs: 0.
Blind-2A/B are forbidden for model selection, threshold tuning and architecture tuning.

## 4. Canonical operator cards
Each known relation has a structural card independent of surface wording:

```text
OperatorCard = {
  family,
  arity,
  directionality,
  functional,
  transitive,
  symmetric,
  temporal,
  causal,
  taxonomic,
  inverse_id,
  subject_role,
  object_role
}
```

Known operators: `owned_by`, `located_in`, `is_a`, `older_than`, `before`, `causes`; `abstain/NOTA` is an open-set outcome, not a world relation.

## 5. Semantic evidence encoder
Inputs:
1. character representation;
2. hashed char n-gram bag (R7.2-inspired, train-only hash space);
3. deterministic morphology/operator evidence (R7.14-inspired);
4. Ω-1.3 subject/object candidate summaries when available;
5. relation phrase residual after masking/replacing arguments with role markers.

The encoder outputs normalized semantic vector `z`.

## 6. Dual canonical prototypes
For relation r:

`p_data(r) = normalize(sum_i w_i z_i / sum_i w_i)`

`p_canon(r) = normalize(W_c c_r)` where `c_r` is the structural OperatorCard vector.

`alpha_r = n_r / (n_r + kappa)`

`p_r = normalize(alpha_r p_data(r) + (1-alpha_r) p_canon(r))`

This prevents rare relations from having only noisy empirical centers and prevents frequent relations from ignoring observed language.

## 7. Prototype geometry
Let P stack relation prototypes. Target similarity geometry G* combines separation and real graph semantics. Training includes:

`L_geometry = ||P P^T - G*||_F^2`

High-confusion pairs (`owned_by/located_in`, `before/causes`, `is_a/owned_by`) receive stronger margin requirements.

## 8. Contrastive paraphrase invariance
Before model code, a separate train semantic bank was frozen with three surface families per relation. It has no normalized-template overlap with Shadow/Blind-2.

Positive pairs: same canonical operator under different surface transformations / argument ordering normalization.
Hard negatives: same entities or similar lexical evidence but different canonical operators.

Weighted supervised contrastive objective:

`L_SC(i) = - mean_p log exp(sim(z_i,z_p)/tau) / sum_a w_ia exp(sim(z_i,z_a)/tau)`

Hard-negative weight increases with prototype similarity and current embedding confusion.

## 9. Equivariance and canonicalization
Transformations that preserve canonical graph meaning must map to the same operator after argument normalization. Example: `B младше A` canonicalizes to `older_than(A,B)`; `После A произошло B` canonicalizes to `before(A,B)`.

Loss: `L_eq = 1 - cos(z(T(x)), R_T z(x))`, with identity `R_T` after canonical role normalization in Stage A.

## 10. Candidate-specific evidence credit
For every relation r create evidence vector:

`e_r=[sim_data, sim_canon, morph_evidence, argument_compatibility, graph_compatibility, prototype_margin, residual_credit]`.

Base score:
`B_r = cos(z,p_r)/tau_r + beta^T e_r`.

A small residual head may produce `Delta_r`; final score is `S_r=B_r+g(x)Delta_r`. Residual corrections never bypass validator/graph authority.

## 11. Open-set / NOTA
The system must not force one of six relations. Use score energy and top-2 margin:

`E(x)=-T log sum_r exp(S_r/T)`.

Return NOTA when dev-calibrated energy/margin/critic thresholds indicate insufficient evidence. Thresholds are selected on Stage-A dev + Shadow-Dev-2 only.

## 12. Relation critic
A small recurrent critic (R7.17-inspired) sees candidate evidence sequence and predicts risk/calibration only. It cannot choose or overwrite the relation. It may cause abstention or request a second semantic trajectory.

## 13. Training objective

`L = L_proto + λc L_hardSupCon + λg L_geometry + λe L_equivariance + λo L_open + λcal L_calibration + λrep L_replay`

Argument extractor is initially frozen. Relation training may not regress Ω-1.3 argument exactness by >1 percentage point on Stage-A dev.

## 14. Model selection
Only Stage-A dev and Shadow-Dev-2 are readable during selection. Primary metric is semantic relation macro-F1 with strict non-abstain graph as guard. Secondary: relation accuracy, NOTA F1, Brier/ECE, argument regression, invalid accepted mutation rate.

## 15. Blind-2 one-shot gate
After checkpoint freeze and SHA:
1. run Blind-2A once;
2. run Blind-2B once;
3. do not tune Ω-1.4 from these results.

Promotion to 250K requires:
- Ω-1.4 relation accuracy > frozen Ω-1.3 baseline evaluated on the same Blind-2 corpus;
- strict non-abstain graph > Ω-1.3 on same corpus;
- NOTA precision >= 98%;
- invalid accepted mutation rate = 0%;
- protected Ω-1.2 regression <= 0 pp;
- argument extraction regression <= 1 pp;
- calibration improves over Ω-1.3 score confidence.

## 16. Scientific boundary
This is a graph-native structured Russian relation experiment, not proof of unrestricted language understanding or AGI. Legacy NEXUS results and current Blind suites are internal benchmarks unless explicitly stated otherwise.
