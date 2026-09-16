# NEXUS Ω-1.5R2 — Universal Subject/Object Binding Cortex — preregistration

Date: 2026-09-16
Base frozen system: Unified NEXUS Rebuild v1
Purpose: fix the measured role-binding bottleneck while preserving the 100% candidate-lattice recall result.

## Scientific boundary

Blind-4 text and labels are forbidden for architecture changes, feature changes, negative-sampling changes, threshold tuning, epoch selection, checkpoint selection, or retraining after opening. Blind-4 is evaluated once after checkpoint SHA-256 is frozen.

## Pre-registered architecture

Ω-1.5R2 scores SUBJECT and OBJECT jointly, not independently.

For a relation r and non-overlapping candidate pair (s,o), the primary learned representation is the whole sentence with the two candidate spans replaced by typed placeholders `<SUBJ>` and `<OBJ>`, prefixed by the canonical relation label. Candidate identity strings are masked from the pair representation. A sparse hashed character/word n-gram encoder feeds an online logistic pair ranker.

Required hard negatives per gold row include:
1. exact swapped gold pair (o,s);
2. gold subject + wrong object;
3. wrong subject + gold object;
4. near-boundary overlapping spans;
5. random non-overlapping candidate pairs;
6. distractor candidates from another clause when present.

Inference ranks joint `(subject, object)` assignments under structural constraints; independent subject/object probability multiplication is not the canonical R2 decision rule.

## Allowed data

Only new `train`, `dev`, and `shadow` splits from the Blind-4 protocol may influence fitting or selection. Historical Blind-A/B from Rebuild v1 remain disclosed historical evidence and are forbidden for R2 tuning.

## Dataset sizes

- train: 150,000
- dev: 12,000
- shadow: 12,000
- Blind-4A: 12,000
- Blind-4B: 3,000

Relations: `owned_by`, `located_in`, `is_a`, `older_than`, `before`, `causes`.

Gold entity spans are 1–4 words. Candidate lattice for R2 must include widths 1–4 and demonstrate >=99.5% both-argument recall on dev and shadow before training is promoted.

## Selection protocol

Checkpoint/hyperparameter selection uses dev + shadow only.
Primary pre-blind score:

`0.45 * both_exact + 0.25 * subject_exact + 0.20 * object_exact + 0.10 * swapped_pair_rejection`

The following may be selected pre-blind only: regularization strength from a fixed small grid, number of online epochs in {1,2,3}, and inference top-K in {12,16,24}. No post-Blind selection is permitted.

## Promotion targets (not guaranteed outcomes)

On one-shot Blind-4, report all metrics. Target gates are:
- candidate both-recall >= 99.5%;
- SUBJECT exact with gold relation >= 80%;
- OBJECT exact with gold relation >= 80%;
- both arguments exact with gold relation >= 70%;
- swapped-gold rejection >= 95%;
- invalid/overlapping accepted pair rate = 0%;
- no tuning_after_open.

A miss is reported as a miss; Blind-4 is never reused for R2 tuning.

## Integration evaluation

After the role checkpoint is frozen, evaluate two paths separately:
1. role-only: gold canonical relation -> R2 binder;
2. end-to-end: frozen Ω-1.4R relation prediction -> R2 binder.

This keeps semantic-relation error separate from role-binding error.
