# NEXUS CRC-R1 — M0/M1 Recovery + Runtime Router Report

**Date:** 2026-09-30  
**Branch:** `crc-r1-foundation`  
**Base:** `unified-v3-generalization-first` @ `a18fa5a58fcd6d3e3bfb7bb7df0b092f13ff940c`

## Executive status

M0 closes the historical-federation audit at **9/11 exact-runnable** with two explicit fail-closed blockers. M1 replaces the canonical MoE runtime's hard-coded heuristic-only routing path with a loader for the already frozen P1 learned router, calibrator and novelty model. The heuristic router remains only as an explicit fallback when P1 artifacts are missing, corrupted, or manifest-incompatible.

This milestone does **not** claim AGI, full 11/11 recovery, or an end-to-end 94.44% runtime score. P1 and B1 are different experiments and remain labelled separately.

## M0 — historical federation

### Exact-runnable when staged against the catalog

R7-L D192, R7.2, R7.6, R7.8, R7.10, R7.14, R7.18, Ω-1.5R2 and V10 600K InfoGraph.

### Fail-closed blockers

- **R7.44.3** — exact final source is present, but transitive R7.38–R7.42 runtime dependencies remain absent, including `r738_x2_latent.pt`, `r738_semantic_governor.joblib` and `r739_task_governor.joblib`. Exact-name searches across Drive and installed GitHub repositories found no bytes.
- **Unified R1.3** — historical sealed evidence exists, but the exact historical release archive remains unavailable. Unified Rebuild v1 and Unified v2 are successors/rebuilds and are not relabelled as R1.3.

## Ω-1.5R2 compatibility recovery

The exact semantic joblib referenced the missing historical import `rebuild_models.SemanticOperatorR`. Inspection of the immutable object state showed only `seed`, `vectorizer`, and `clf`. The compatibility shell restores the original inference contract:

```python
class SemanticOperatorR:
    def predict(self, texts):
        return self.clf.predict(self.vectorizer.transform(texts))
```

No weights, thresholds or learned state are reconstructed.

Behavioral replay with the exact frozen artifact reproduced Ω-1.4R relation accuracy on the Blind-4 corpora exactly:

- Blind-4A: **0.6016666667** over **12,000** cases
- Blind-4B: **0.6670000000** over **3,000** cases

The exact Ω joint binder loads successfully and the archived Ω suite ran **12 passed**. Recovered V10 hashes match its catalog, its archived suite ran **3 passed**, and its exact solver completed a checkpoint-backed ARC smoke case.

## M1 — learned router integration

The canonical six-expert P1 artifacts already exist under `artifacts/v3_moe/p1`. Their accepted report records useful-expert recall **99.62%**, strict routing **98.80%**, heuristic Top-K recall **79.50%**, novelty AUROC **0.999966**, and calibration ECE **0.052251**. These are routing-curriculum metrics, not an end-to-end AGI score.

`LoadableCapabilityRouter` now verifies SHA-256, feature/expert manifest order, loads router + calibrator + novelty together, uses learned novelty only for routing width, fails closed to `HeuristicCapabilityRouter`, and exposes fallback provenance. The seven-expert B1 router remains scientifically separate.

## Next gate

M2 is CRC-R1 foundation: immutable cognitive state, hierarchical memory with raw provenance, compositional program AST, bounded future tree, central RPE, recursive cognitive credit graph, capability self-model, metacontrol and three-speed continual-learning gates.

FTX1 remains sealed.
