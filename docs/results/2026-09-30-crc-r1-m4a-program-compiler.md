# CRC-R1 M4a — typed compositional AST compiler

**Date:** 2026-09-30

M4a connects the new compositional program representation to the existing V3 executor without pretending that unsupported higher-order nodes already have semantics.

## Executable subset
The compiler accepts typed rule atoms for TRANSITIVE, SYMMETRIC, INVERSE and COMPOSITION. SEQUENCE/COMPOSE AST containers aggregate independently typed clauses.

## Fail-closed boundary
IF, INHIBIT, TEMPORAL and COUNTERFACTUAL remain `UNSUPPORTED` until dedicated typed semantics are implemented. Unknown rule atoms are `MALFORMED`. No nearest-rule or name-similarity fallback exists.

## Verification
CRC test suite with the exact current V3 contracts/rule algebra/executor: **13 passed**.

Verified:
- transitive AST executes a two-hop proof;
- inverse AST executes reverse relation;
- multi-clause AST aggregation;
- nonce operator renaming preserves rule shape;
- unknown/higher-order nodes fail closed.

This is intentionally M4a, not a claim that the full HARD-OOS D program space has been solved.
