# NEXUS-FTX1

NEXUS-FTX1 is the frozen far-transfer gate for Unified v3 Generalization-First.

The public repository contains only the runtime schema, scorer, DEV/SHADOW generators, structural validators, red-team baselines and the freeze manifest. The exact Family-C BLIND generator, runtime corpus and scorer-only gold are sealed outside the development branch.

## Frozen blind

- 2,400 cases total
- 8 tracks x 300 cases
- DEV seed: `11017`
- SHADOW seed: `22017`
- BLIND seed: `33017`
- runtime-visible fields: `case_id`, `prompt`, `history`, `documents`
- forbidden gold-adjacent metadata is scorer-only

Tracks:

1. `semantic_rule_induction`
2. `surface_far_transfer`
3. `role_voice_coreference`
4. `task_schema_induction`
5. `compositional_reasoning`
6. `cross_language_transfer`
7. `long_horizon_transfer`
8. `evidence_counterfactual`

The canonical hashes and per-track hashes are in `frozen/NEXUS_FTX1_FREEZE_MANIFEST.json`.

## Red-team veto

The freeze is valid only when all registered shortcut attacks stay below their thresholds and normalized grammar overlap with DEV/SHADOW stays <= 5%. Any inspection or tuning on sealed BLIND content before the one-shot Unified v3 evaluation invalidates FTX1 and requires a successor freeze.

## Development rule

Do not place BLIND cases, BLIND gold or the Family-C generator in the Unified v3 source branch. Unified v3 may use DEV and SHADOW only. The sealed BLIND suite is opened exactly once after the v3 preblind checkpoint is frozen.
