# CRC-R1 M13 — External Action Authority Boundary

**Date:** 2026-09-30

NEXUS now has an explicit boundary between cognition and side effects.

## Law

`NEXUS thinks and proposes.`

`AUTOPILOT / META-OS authorizes and executes.`

The cognitive core can create an immutable `ActionProposal` containing action type, target, typed arguments, reason, evidence IDs, risk, estimated cost and requested scope. The proposal has a canonical SHA-256.

It cannot execute that proposal.

## Permit binding

An external `ExecutionPermit` must be bound to the exact proposal hash and constrain:
- issuer and policy;
- allowed action types;
- allowed scopes;
- maximum risk;
- maximum cost;
- explicit approval references for medium/high-risk effects.

Any proposal mutation after approval changes its hash and invalidates the permit.

## Result

The architecture boundary is now explicit in code:

`CognitiveLoop → ActionProposal → META-OS permit → AuthorizedAction → AUTOPILOT executor`

The `AuthorizedAction` object still does not perform the side effect. Execution remains outside the NEXUS reasoning package.

This prevents future planning, recursive credit or a generative model from silently acquiring tool authority.
