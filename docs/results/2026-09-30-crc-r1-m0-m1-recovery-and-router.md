# NEXUS CRC-R1 — M0/M1 Recovery + Runtime Router Report

**Date:** 2026-09-30  
**Branch:** `crc-r1-foundation`  
**Base:** `unified-v3-generalization-first` @ `a18fa5a58fcd6d3e3bfb7bb7df0b092f13ff940c`

## Executive status

M0 is now split into two non-interchangeable ledgers: **historical byte-identical recovery = 10/11** and **operational verified federation = 11/11 READY**. R7.44.3 is recovered as an exact deployed runtime; the operational authority slot is satisfied by R1.3-X V2/V3. The only remaining historical identity gap is the original byte-identical Unified R1.3 release tree. M1 replaces the canonical MoE runtime's hard-coded heuristic-only routing path with a loader for the already frozen P1 learned router, calibrator and novelty model. The heuristic router remains only as an explicit fallback when P1 artifacts are missing, corrupted, or manifest-incompatible.

This milestone does **not** claim AGI or byte-identical historical 11/11 recovery. It does establish **operational verified 11/11**. The original Unified R1.3 release identity remains distinct from R1.3-X. P1 and B1 are different experiments and remain labelled separately.

## M0 — federation recovery

### Historical byte-identical ledger — 10/11

Accepted historical/deployed identities:

R7-L D192, R7.2, R7.6, R7.8, R7.10, R7.14, R7.18, **R7.44.3 EXACT_DEPLOYED_RUNTIME**, Ω-1.5R2 and V10 600K InfoGraph.

The only remaining historical identity gap is the **original Unified R1.3 release tree**. It remains fail-closed and is not silently substituted by a later system.

### Operational verified ledger — 11/11 READY

The operational authority slot is satisfied by **R1.3-X V2/V3 VERIFIED_OPERATIONAL_RUNTIME**.

Recovery provenance:
- PR #6 head `4735ca4f36d441f4fa2de6af4c704d5140a6c586` — exact cognitive Russian runtime using frozen R7.6/R7.8/R7.10/R7.14 organs;
- PR #7 head `105a692d64a42d6c772de69dcaeb16ac27833b01` — compositional authority governor;
- `AUTHORITY-CONFLICT-V3-B2 = 12/12` frozen first-open, no post-open tuning;
- Google Drive archive slot `05_R1_3_X_VERIFIED_RUNTIME`.

R1.3-X is accepted for the **operational authority slot** only. It is not relabelled as the byte-identical historical Unified R1.3 release.

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
