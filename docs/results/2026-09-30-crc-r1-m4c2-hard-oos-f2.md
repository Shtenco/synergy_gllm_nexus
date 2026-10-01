# CRC-R1 M4c.2 — HARD-OOS F2 Negative-Semantics Protocol

**Date:** 2026-09-30

HARD-OOS F v1 had already entered development history before explicit negative semantics were added. Rather than mutate an opened benchmark, F2 is a new sealed family.

F2 preregisters six negative/open-world higher-order strata:

1. `if_false`
2. `inhibit_open`
3. `cf_flip_false`
4. `cf_remove_unknown`
5. `nested_negative_gate`
6. `mixed_negative_cf`

The runtime corpus contains AST, world and task only. Expected status/truth remain scorer-only and are SHA-frozen before execution.

Scientific distinction:
- FALSE is represented only by an explicit negative fact or counterfactual polarity flip;
- UNKNOWN remains `None`;
- no closed-world negation is used;
- fixed-basis baseline reports representation failure for every higher-order case.

This protocol is intended to become a validation.v3 prerequisite. FTX1 remains sealed.
