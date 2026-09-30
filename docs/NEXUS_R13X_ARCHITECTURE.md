# Unified R1.3-X

## Core loop

Input → V4.2 semantic graph encoding → Blackboard → learned capability router → parallel expert proposals → V7.2 exact verification → causal/world-state check → authority/evidence governor → answer graph → Russian renderer.

## Immutable expert contracts

Every expert returns:

- proposal;
- confidence;
- uncertainty/OOD signal;
- supporting graph nodes/edges;
- provenance;
- executable verification operation.

The router may propose several experts. It may not suppress a higher-authority exact result merely because a neural expert has higher raw confidence.

## Three-pass cognition

### Pass A — semantic
V4.2-style graph representation produces entities, relations, operation candidates and uncertainty.

### Pass B — hypothesis
Sparse routing selects semantic, exact, formal, memory, causal, world and language experts. Competing hypotheses are retained instead of prematurely collapsing to one answer.

### Pass C — verification
V7.2 executes exact operations where possible. Causal interventions and world-state consistency are applied before final authority resolution.

## Authority

EXACT_VERIFIED > DIRECT_EVIDENCE > CAUSAL_CONSISTENT > MEMORY_SUPPORTED > NEURAL_PROPOSAL > SURFACE_GUESS.

This is a precedence rule, not a model score.

## Open-set behavior

If no hypothesis clears the verification threshold, the system abstains and exposes the missing evidence/operation instead of inventing an answer.

## Memory

Separate:

- immutable historical events;
- current world state;
- derived beliefs;
- provenance edges.

Contradictory updates retract active world facts while preserving historical records.

## Learning

Train routing and representation layers; never train on blind suites. Frozen benchmark manifests remain immutable.

## Required regression gates

- exact-core regression;
- contradiction regression;
- memory revision regression;
- causal intervention regression;
- OOD/abstention regression;
- Russian semantic preservation;
- end-to-end replay against frozen evidence.

## Deployment modes

ORIGINAL: historical artifact only.
AUGMENTED: original expert + new verifier.
LEARNED: trained router/representation.
FULL: all components with authority governor.

Historical artifacts are never silently replaced by upgraded versions.
