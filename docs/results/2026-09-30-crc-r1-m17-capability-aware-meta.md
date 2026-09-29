# CRC-R1 M17 — Capability-Aware Meta-Control

**Date:** 2026-09-30

Self-audit found that the foundation MetaController accepted a SelfModel argument but did not materially use it. M17 closes that false integration.

The controller now receives optional capability hints and reads empirical reliability from `NexusSelfModel`.

A weak capability contributes:

`capability_difficulty = 1 - min(reliability(capability_hints))`

to overall task hardness alongside novelty and uncertainty.

Consequences:
- weak capabilities can increase branch depth;
- widen expert Top-K;
- increase memory budget;
- increase verification level;
- trigger abstention when both known weakness and uncertainty are extreme.

Strong capabilities do not automatically consume extra compute.

The Cognitive Loop now carries `capability_hints` in the request and records verification level / weak capabilities in its immutable trace.

This makes SelfModel operational rather than decorative.
