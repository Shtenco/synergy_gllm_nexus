# CRC-R1 M6 — Recursive Credit Learning

**Date:** 2026-09-30

M6 turns the CRC credit graph from an explanation log into a learning signal.

## Mechanism
For every outcome:
1. compute RPE;
2. propagate credit backward through the CognitiveTraceGraph;
3. optionally compute/accept counterfactual leave-one-out credit;
4. blend propagated and counterfactual credit;
5. update per-node running credit statistics;
6. update the capability SelfModel.

This distinction matters because pure graph propagation cannot tell apart two correlated contributors that both lie on the same successful path. Counterfactual credit can assign positive responsibility to the causal contributor and negative responsibility to a spurious contributor.

## Learned statistics
Each node keeps count, mean credit, positive mass, negative mass and a bounded trust transform. Rankings can be queried per component kind.

## Runtime integration
`CognitiveRecursiveCoreR1.close_episode(...)` now invokes `RecursiveCreditLearner`. Credit therefore persists across episodes instead of disappearing after one trace.

## Scientific boundary
This is component-level online reliability learning. It does not yet mutate neural weights. Weight changes remain behind the SLOW continual-learning promotion gate.

Next: M7 promotion/consolidation controller with replay and anti-forgetting evidence.
