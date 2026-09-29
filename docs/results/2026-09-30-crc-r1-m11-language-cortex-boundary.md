# CRC-R1 M11 — Language Cortex → Semantic IR Proposal Boundary

**Date:** 2026-09-30

Natural conversation needs a stronger input-language cortex as much as it needs a fluent output cortex. The historical `ControlledSurfaceAdapter` is intentionally narrow, so M11 adds a safe interface for future neural/free-text parsing.

## Core rule

A language model may propose Semantic IR. It may not commit world facts.

`raw user text → Language Cortex → proposal → admission → SemanticObservation(PROPOSAL_ONLY)`

The result contains the SHA-256 of the input, backend identity and typed atoms, but no raw-text field. `assert_text_quarantined` is applied before the proposal leaves the language boundary.

## Admission checks

- input hash must match the actual message;
- backend identity required;
- atom count bounded;
- operator IDs structurally valid;
- arity > 0;
- arguments bounded/no control characters;
- confidence above threshold;
- every proposed atom carries a source-span digest.

Rejected proposals yield an empty SemanticObservation and remain fail-closed.

## Baseline

The existing controlled V3 parser is wrapped as `ControlledLanguageBackend` so the old deterministic behavior can use the same proposal-only contract.

## Authority boundary

M11 deliberately does not modify the world or persistent memory. A later semantic/authority stage must decide which proposal, if any, becomes a committed fact.

This is the required ingress counterpart to M9's authority-safe generative egress.
