# CRC-R1 M10a — Unified Cognitive Loop

**Date:** 2026-09-30

CRC-R1 components are now connected through a single typed deliberation/observation loop.

## Deliberation

`CognitiveLoopR1.deliberate()` performs:

1. create immutable `NexusCognitiveState`;
2. MetaController allocates depth/fanout/expert/memory budget;
3. hierarchical memory retrieval;
4. typed compositional/higher-order program execution;
5. learned Future Planner when a world model is available;
6. construct a CognitiveTraceGraph linking meta → memory → program → branch → answer.

The authority-owned world is read-only during deliberation.

## Observation

`observe()` is the learning boundary:
- external/task reward is supplied after the decision;
- RPE is computed;
- outcome is attached to the trace;
- recursive/counterfactual credit updates component reliability;
- SelfModel is updated.

This closes the loop that previously existed only as separate modules:

`state → memory → meta → program → future → answer → outcome → RPE → credit → self-model`.

## Remaining boundary

This loop is still typed/controlled. It is not yet a natural-language autonomous agent and does not have external action authority. The generative cortex remains surface-only, and slow neural updates remain behind the M7 promotion gate.

Next: M10b fresh integrated META-OOS benchmark over the loop, without FTX1.
