# M32 — Generalized Semantic + Task Ingress — FINAL POST-REVIEW EVIDENCE

**Date:** 2026-10-01  
**Frozen CRC-R1 base:** `fded8bd46777b2e868620b4c85d60c5c375b5ec1`  
**Reviewed M32 implementation:** `0ef170b88f29abf4d24aa52685b35a4bd9b6f32d`  
**CI-only evidence head:** `b7e14d478ca22e503e85c886ee18eafa30262b20`

## Canonical status

M32 engineering architecture is **GREEN** after final self-review hardening.

Final review added explicit rejection for:
- higher-order `query_operator` smuggling;
- malformed `ATOM` symbols that are not a recognized typed rule.

No frozen R1 reasoning code was changed.

## Independent post-review evidence

### Linux pinned evidence

Workflow run: `36917598158`  
Artifact: `m32-evidence-0ef170b8`  
Artifact ID: `11191032078`  
Artifact SHA-256: `3c6cada8912d5a4650617bdedabd356fbf29a589942c13b7ef727387c14bcce1`

### Windows pinned evidence

Workflow run: `36917598270`  
Artifact: `m32-evidence-windows-0ef170b8`  
Artifact ID: `11191187337`  
Artifact SHA-256: `638de730ca3e635a661f828980c2e202d41e48d9478bd4df17d974d8620ff0d7`

Both workflows checked out exactly:

`0ef170b88f29abf4d24aa52685b35a4bd9b6f32d`

and completed successfully.

## M32-DEV architecture result

```text
benchmark                         M32-DEV
seed                              32001
cases                             180
clean_oos                         false
neural_quality_claim              false
ftx1_used_as_clean_oos            false

task_admission                    1.0000
provenance_validity               1.0000
program_admission_solvable        1.0000
e2e_strict_solvable               1.0000
unsafe_authority_promotions       0
```

This is an **engineering fixture** result: it proves the typed ingress/authority/program/CRC pipeline works under correct deterministic proposals. It is not a real neural-model quality claim.

## Fresh M32-META freeze

```text
schema                            nexus.m32.meta.freeze.v1
benchmark                         M32-META
seed                              32991
case_count                        240
generator_sha256                  b0181d22ae1dbf7a2a0a814ca7b463b3dc46cf3654452b055f5af267a08e8db1
implementation_commit             0ef170b88f29abf4d24aa52685b35a4bd9b6f32d
sealed_before_first_integrated_evaluation true
test_open_count                   0
ftx1_status                       CONSUMED_FTX1
ftx1_used_as_clean_oos            false
ftx2_authored                     false
```

M32-META remains unopened for the real neural proposal path.

## Regression evidence

Linux pinned evidence:

```text
pytest tests/m32 -q
43 passed

pytest tests/crc_r1 tests/hard_oos_f tests/hard_oos_f2 tests/crc_meta_g -q
153 passed
```

Windows pinned evidence:

```text
pytest tests/m32 -q
43 passed in 2.14s

pytest tests/crc_r1 tests/hard_oos_f tests/hard_oos_f2 tests/crc_meta_g -q
153 passed in 4.94s
```

Normal PR CI is also GREEN on Linux and Windows, with compileall PASS.

## Frozen R1 non-regression

Both pinned evidence workflows verified no source diff in:

`src/nexus_gllm/unified_v3/cognitive/conversational_reasoner.py`

relative to frozen base `fded8bd46777b2e868620b4c85d60c5c375b5ec1`.

Current Windows evidence source SHA-256:

`36c61e0ac63e01ddb6e97ab25a6e91e026675650ab8555318a29bd7d76a64b6f`

The important invariant is the zero git diff to frozen R1; M32 adds `ConversationalReasonerR2` instead of rewriting R1.

## Scientific boundary

Demonstrated:
- grounded multi-source ingress contracts;
- Unicode-safe provenance spans;
- duplicate/unknown source fail-closed;
- transient ASSERTED_CONTEXT without durable authority escalation;
- typed task admission;
- typed program AST admission;
- operator-smuggling prevention including `query_operator`;
- malformed-ATOM rejection;
- end-to-end execution through existing CRC under admitted fixture proposals;
- zero frozen CRC-R1 regression in the tested suites.

Not yet demonstrated:
- quality of a real neural proposal model;
- broad free-form RU/EN extraction accuracy in the wild;
- first-open M32-META neural performance;
- untouched FTX2 performance.

## Next gate: M32.1 Neural Proposal Quality

A pre-existing model pin from 2026-09-24 is available and predates M32/FTX2:

```text
model             Qwen/Qwen3.5-0.8B
GGUF repo         bartowski/Qwen_Qwen3.5-0.8B-GGUF
file              Qwen_Qwen3.5-0.8B-Q4_K_M.gguf
expected SHA-256  fb044e93939a70469c905781334f5de1e6c8b608ced6cbc8c9249bd4127d9526
```

M32.1 must first verify the actual model bytes against this hash, evaluate neural proposals on M32-DEV, then — only after model/backend/prompt/runtime are frozen — open M32-META once. FTX1 remains consumed and unavailable for tuning. FTX2 is not authored yet.
