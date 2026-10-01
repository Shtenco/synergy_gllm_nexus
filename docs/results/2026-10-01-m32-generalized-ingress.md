# M32 — Generalized Semantic + Task Ingress

This report is superseded by the post-review canonical evidence:

`docs/results/2026-10-01-m32-generalized-ingress-final.md`

Canonical reviewed implementation:

`0ef170b88f29abf4d24aa52685b35a4bd9b6f32d`

Post-review status:

```text
M32 tests                 43 / 43 PASS
Frozen regressions       153 / 153 PASS
Linux pinned evidence             PASS
Windows pinned evidence           PASS
M32-DEV architecture gates        PASS
M32-META                  SEALED, open_count=0
ConversationalReasonerR1          NO DIFF vs frozen CRC-R1
FTX1                              CONSUMED, not reused
```

Important scientific boundary: the 100% M32-DEV result is a deterministic fixture/architecture result, **not** a real neural-model quality claim. The next gate is M32.1 Neural Proposal Quality using a model artifact pinned before M32/FTX2.
