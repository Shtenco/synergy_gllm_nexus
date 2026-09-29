# CRC-R1 M12 — Semantic Commit Authority Gate

**Date:** 2026-09-30

M11/M11b deliberately made neural/free-text parsing proposal-only. M12 adds the separate authority transition from proposed Semantic IR to committed world facts.

## Authority law

Parser confidence is **not** truth confidence.

A proposed atom becomes `VERIFIED` only by one of two paths:

1. trusted formal proof; or
2. at least two independent trusted evidence lineages.

Two sources from the same lineage do not count as independence.

A trusted contradiction blocks commit.

## User statements

A user assertion may become `ASSERTED_CONTEXT`, which is useful for dialogue state, but it is not silently promoted to `VERIFIED` world truth. This keeps:

`"the user said X"`

separate from:

`"NEXUS verified X"`.

## Model proposals

`MODEL_PROPOSAL` attestations never grant commit authority on their own, regardless of model confidence.

## Result

The ingress authority chain is now explicit:

`raw text → language proposal → span grounding → Semantic IR proposal → independent authority gate → VERIFIED world fact / ASSERTED context / reject`.

This closes the main parser-to-world privilege escalation path before mounting a strong language model.
