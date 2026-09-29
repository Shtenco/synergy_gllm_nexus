# CRC-R1 M15 — Causal Model / Intervention Evidence

**Date:** 2026-09-30

Counterfactual execution existed before CRC could justify a causal edge. M15 adds an evidence-weighted causal graph that distinguishes observational association from interventional evidence.

## Causal evidence classes

- OBSERVATIONAL
- INTERVENTIONAL
- COUNTERFACTUAL

A strong observational correlation contributes context but **cannot identify causality by itself**.

An edge becomes `identified=True` only when preregistered interventional mass and total causal evidence thresholds are met and causal support exceeds trusted contradiction mass.

## Intervention ledger

`InterventionLedger` records:
`do(variable=value) → observed effects`

and converts those observations into typed interventional evidence.

## Structural operations

The graph exposes:
- identified parents;
- identified descendants;
- cycle detection for proposed causal additions.

Only identified edges propagate through descendant traversal.

## Benchmark

The M15 controlled benchmark creates pairs with equally strong observational correlation. Half remain causal under intervention; half collapse under intervention. The correlation-only control therefore cannot solve the distinction, while the intervention-aware graph can.

This is still controlled causal-identification mechanics, not proof that NEXUS can discover arbitrary real-world causality.

Next: M16 active information-gain query selection over uncertain beliefs/causal hypotheses.
