# CRC-R1 M4b — Higher-Order Cognitive Execution

**Date:** 2026-09-30  
**Branch:** `crc-r1-foundation`

M4b gives explicit typed execution semantics to the four AST operators that M4a intentionally left non-executable.

## Semantics

- `IF(condition, body)`: body runs only when the condition is proved. False conditions stop; unresolved conditions remain unresolved.
- `INHIBIT(blocker, body)`: a proved blocker suppresses the body. An unresolved blocker fails closed.
- `TEMPORAL(child, mode=current|time=N)`: the child executes against a materialized snapshot from the existing `TemporalLedger`.
- `COUNTERFACTUAL(child, typed intervention)`: the child executes in a cloned world produced by the existing `CounterfactualEngine`; the actual world is not mutated.

Primitive rule atoms are still delegated to the existing V3 `Executor`. Higher-order execution therefore composes existing semantics rather than introducing a benchmark-specific solver.

## Compiler boundary

`CognitiveProgramCompiler` now distinguishes:
- `execution_mode=rule_program` for the M4a primitive subset;
- `execution_mode=higher_order` for a structurally valid higher-order tree;
- `MALFORMED` for unknown rule atoms or invalid arity.

Higher-order trees are not flattened into a `RuleProgram`, because flattening would destroy conditional, inhibitory, temporal and counterfactual semantics.

## Negative controls

- unresolved IF conditions do not execute the body;
- unresolved inhibitors do not silently open the path;
- malformed/partial query overrides fail closed;
- unsupported intervention kinds fail closed;
- counterfactual execution leaves the actual world unchanged.

## Next gate

M4c / HARD-OOS F must use never-seen AST topologies and scorer-isolated generation. It must compare the old fixed-basis representation against CRC compositional execution without using HARD-OOS D as a tuning set.

FTX1 remains sealed.
