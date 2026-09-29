# CRC-R1 M24 — Task / Intent Cortex Boundary

**Date:** 2026-09-30

M23 connected language ingress and guarded egress, but free-text semantic extraction alone does not identify what operation the user is asking NEXUS to perform. M24 adds a separate proposal-only Task Cortex.

A backend proposes:
- TaskOpcode;
- optional operator ID;
- typed arguments;
- confidence;
- source span bound to the exact input SHA.

The gate validates span grounding, confidence, operator syntax, argument bounds and opcode-specific shape. Rejected task proposals fail closed and produce no TaskProgram.

Like the Language Cortex, the Task Cortex has no execution authority. It can propose a typed task, not answer it and not mutate the world.

A tiny deterministic Russian query baseline is included only so the interface has a non-neural reference implementation. A future neural intent model must use the same contract.

The ingress architecture is now split correctly:

free text
→ semantic proposal (what facts are mentioned)
→ task proposal (what operation is requested)
→ independent authority / reasoning.

This avoids asking one generative model to silently own parsing, intent, truth and execution at once.
