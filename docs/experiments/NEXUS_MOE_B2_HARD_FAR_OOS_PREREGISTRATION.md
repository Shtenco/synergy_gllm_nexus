# NEXUS-MOE-B2 / HARD-FAR-OOS — preregistration

**Status:** SEALED-BEFORE-GENERATION / FAIL-CLOSED

B2 is the next benchmark after NEXUS-MOE-B1. B1 reached 94.44% on six known capability families, so B2 must test transfer outside those routing families rather than re-measure specialist recognition.

## Artifact gate

The benchmark generator and blind test opening are forbidden until all 11 requested historical organs pass the artifact catalog.

Accepted provenance states:

- `EXACT_RUNNABLE`
- `EXACT_DEPLOYED_RUNTIME` for a byte-identical released runtime when the original authoring-language runtime is transitively unavailable.

Current recovery state at preregistration:

- R7-L — exact
- R7.2 — exact
- R7.6 — exact
- R7.8 — exact
- R7.10 — exact
- R7.14 — exact
- R7.18 — exact
- R7.44.3 — exact deployed mobile runtime recovered from `SINERGIYA-FINANS-v8.0.1-NEXUS-R7443-MAX.apk`, SHA-256 `d248bb75c45694bbde6914615243080b711d2efea80b22c2652e692cc8307703`; six frozen contract families replayed locally as 8/8 checks
- Ω-1.5R2 — exact
- V10 600K — exact
- Unified R1.3 — BLOCKED: historical sealed evidence exists, but the original release tree has not yet been recovered. `NEXUS Unified RU v1` and `Unified NEXUS Rebuild v1` are successors and must not be relabelled as R1.3.

Therefore B2 readiness is **10/11**, not 11/11.

## HARD-FAR-OOS constraints

The final blind families must be generated only after the 11/11 gate and must not reuse B1 family templates, FTX1 BLIND, HARD_OOS_D, or scorer-visible gold shortcuts.

Required novelty axes:

1. new task semantics, not merely paraphrases;
2. new surface forms;
3. new composition of at least two capabilities per case;
4. held-out operator/relation vocabulary;
5. temporal/context perturbations;
6. adversarial evidence conflicts;
7. counterfactual world updates;
8. cross-domain procedural induction.

Primary metrics will be strict end-to-end accuracy, negative transfer, abstention calibration, per-novelty-axis accuracy, and distance to an oracle-expert ceiling. No post-open tuning is permitted.

## Scientific boundary

A good B2 result will support far-transfer claims only for this frozen benchmark distribution. It will not by itself establish unrestricted AGI or open-domain language competence.
