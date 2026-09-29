# CRC-R1 M4c — HARD-OOS F

**Date:** 2026-09-30

HARD-OOS F is a new higher-order topology benchmark for CRC-R1. It does not reuse HARD-OOS D as a clean OOS set and does not touch FTX1.

## Goal
Test the architectural question exposed by HARD-OOS D: can the system represent and execute higher-order programs whose topology is outside the old fixed rule basis?

## Strata
- nested_if_cf
- temporal_if
- inhibit_cf
- temporal_inhibit
- deep_mixed
- surface_nonce

Every case requires higher-order representation. Surface symbols are nonce-renamed so operator identity is not a shortcut.

## Isolation
Runtime records contain only AST, world, task, temporal ledger and stratum. Expected status/truth and topology hashes live only in scorer-only gold. Runtime and gold are SHA-frozen before execution.

## Baselines
The historical fixed-basis comparator is intentionally honest: because IF/INHIBIT/TEMPORAL/COUNTERFACTUAL are not representable in the old rule basis, it returns `REPRESENTATION_FAILURE`. It is not given a hidden benchmark-specific emulator.

CRC-R1 executes through the M4b typed higher-order interpreter.

## Metrics
- strict status+truth accuracy
- status accuracy
- representation-failure rate
- per-stratum accuracy
- unique topology count

## Scientific boundary
The benchmark generator and CRC executor are both internal code, so a one-shot result is evidence for this architecture/protocol, not proof of broad reasoning or AGI. The stronger next benchmark should independently author AST generators and adversarial semantic worlds.

FTX1 remains sealed.
