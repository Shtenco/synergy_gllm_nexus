# NEXUS Federation Max Train

This branch contains the maximal safe training curriculum prepared on 2026-10-20.

## Ground truth from the existing OMEGA_20X checkpoint

Existing checkpoint:
- Drive folder: NEXUS_OMEGA_20X_CHECKPOINTS
- checkpoint: last.pt
- step: 8102
- parameters: 13,305,097
- CUDA-trained
- first epoch not completed
- test token accuracy about 0.887
- free generation is not coherent
- public new-grammar OOD diagnostic: 0/32
- memory-on and memory-off token metrics are nearly identical

Therefore the checkpoint is preserved and must not be blindly extended on the same token stream.

## Training order

1. Federation router / novelty / calibration
2. Russian SFT replay-balanced curriculum
3. Verified reasoning curriculum
4. ARC / operator induction curriculum
5. Proof DAG / evidence distillation
6. Structural causal + counterfactual curriculum
7. Long-horizon planning curriculum
8. Memory/context curriculum
9. Federation teacher distillation
10. Continual-learning replay and promotion gates

## CPU-compatible stage

Run:

python -m training.federation_max_train --router-only

This trains:
- learned router
- novelty detector
- expert calibrator

with larger train/dev/OOS sets and promotion gates.

## Neural checkpoint continuation

Do NOT resume last.pt with an approximate reimplementation.

The original checkpoint was created by a separate source tree named nexus_omega_20x. The surviving traceback references:
- /content/nexus_omega_20x/curriculum_v3.py
- /content/nexus_omega_20x/data.py

Those source files are not currently present in the Drive checkpoint folder and were not found by Drive search.

Required before neural continuation:
- recover exact original nexus_omega_20x model/trainer code, OR
- explicitly perform a documented migration/distillation into a new architecture instead of pretending it is a resume.

## Data policy

Training may use:
- NEXUS_RU_SFT_450MB
- DEV-only verified reasoning generators
- teacher outputs from federation components
- replay buffers from historical capabilities

Training must NOT consume:
- consumed FAR-OOS blind corpora as new evidence
- consumed second-blind corpus as new evidence
- Third Blind corpus before freeze
- FTX2 (still unauthored)
- M32-META (still sealed)

## Promotion

A neural candidate is promoted only when generation-level and reasoning-level gates pass, not merely token loss/accuracy.

See training/federation_max_curriculum.json.
