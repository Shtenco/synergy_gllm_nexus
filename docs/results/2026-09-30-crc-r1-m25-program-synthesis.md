# CRC-R1 M25 — Evidence-Ranked Program Synthesis Cortex

**Date:** 2026-09-30

M24 can propose a typed TaskProgram from free text, but the reasoning AST still had to be supplied externally. M25 adds the first program-synthesis cortex over CRC ProgramNode trees.

## Generation

Candidate structures are generated from operators present in the world/task:
- transitive and symmetric atoms;
- cross-operator inverse candidates;
- cross-operator composition candidates;
- small SEQUENCE compositions.

The representation is ProgramNode AST, not the historical fixed RuleFamily hypothesis state.

## Selection

Programs are scored only against separate demonstration/evidence cases. The current target's gold answer is never an input to synthesis.

Score combines:
- evidence fit;
- contradiction penalties;
- unresolved penalties;
- AST complexity cost.

With no evidence, the cortex returns no selected program rather than guessing a sovereign rule.

## Scientific boundary

This is search-based compositional synthesis, not yet a learned neural program proposer. Its significance is architectural: target execution no longer requires benchmark code to hand NEXUS the correct rule program.

A future learned proposer/ranker can generate the same ProgramNode contract and remain subject to execution/evidence verification.
