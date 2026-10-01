# NEXUS-MOE-B2 M3b — Frozen P1 adapter

**Date:** 2026-09-30

The sealed B2 benchmark can now execute the exact six-expert P1 architecture without exposing scorer-only gold to the router.

## Frozen input contract
B2's eight continuous features map directly to the P1 order:
`support, ru, evidence, context, graph, novelty, proof, cost`.

The adapter supplies continuous `ru_signal` and `evidence_signal`, while semantic booleans are retained only for the heuristic interface. This prevents accidental quantization of the frozen learned model.

## Abstention gate
Before one-shot opening the following fixed gate is preregistered:
- learned novelty probability >= 0.80
- top calibrated expert probability < 0.55

Only then is the route marked abstain.

## Integrity boundary
The adapter refuses to run unless `LoadableCapabilityRouter` verifies the P1 payload against an integrity manifest. It never silently evaluates B2 with heuristic fallback.

The next step is CI-generated integrity + one frozen B2 execution. No B2 score is claimed in this commit.
