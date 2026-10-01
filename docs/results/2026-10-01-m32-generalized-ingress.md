# M32 — Generalized Semantic + Task Ingress

**Date:** 2026-10-01  
**Branch:** `m32-generalized-ingress`  
**Frozen CRC-R1 base:** `fded8bd46777b2e868620b4c85d60c5c375b5ec1`  
**Verified M32 implementation commit:** `6dd69420c4ea20ec64da38f7056c39d543216b77`  
**Evidence workflow:** `m32-evidence`, run `36914262398`  
**Evidence artifact:** `m32-evidence-6dd69420`, artifact ID `11188567780`, artifact ZIP SHA-256 `4d6d48cfc1266595695af28554629016c0d958629fb781c2f106473b8c5ff333`

## Status

M32 is **engineering-complete for the proposal/admission/orchestration architecture**.

It is **not** a claim that a real neural ingress model already achieves the DEV scores below. The M32-DEV benchmark intentionally uses a deterministic fixture proposal backend to test whether the authority/provenance/task/program/CRC plumbing is correct. `neural_quality_claim=false` is part of the emitted report.

FTX1 is consumed and was not used as clean OOS, training data, threshold selection, or a DEV/META generator source.

## Implemented path

```text
RU / EN prompt
+ dialogue history
+ documents
        ↓
GeneralizedIngressBackend (proposal-only)
        ↓
source/hash/span validation
        ↓
semantic atom proposals
TaskProgram proposal
ProgramNode proposal
        ↓
SemanticCommitGate
        ↓
ReasoningContextView
  durable verified context
  + transient ASSERTED_CONTEXT execution view
        ↓
ProgramProposalGate
        ↓
ConversationalReasonerR2
        ↓
CognitiveLoopR1
        ↓
epistemic result + safe surface
```

`ConversationalReasonerR1` remains unchanged from the frozen CRC-R1 base.

## Components

- `generalized_ingress.py` — multi-source immutable envelopes, source SHA-256, Unicode/Python-character grounded spans, semantic/task proposals and fail-closed admission.
- `reasoning_context.py` — authority-preserving transient reasoning context; asserted context may participate in execution without durable promotion.
- `program_proposal.py` — recursive AST admission, provenance checks, complexity bounds and operator-smuggling prevention.
- `generalized_ingress_ollama.py` — one-call, temperature-zero, digest-pinned, proposal-only Ollama adapter.
- `conversational_reasoner_r2.py` — orchestration into the existing CRC reasoning stack without changing R1 behavior.
- `benchmarks/m32_dev/*` — fresh engineering DEV corpus.
- `benchmarks/m32_meta/*` — independent META generator and pre-evaluation freeze tooling.

## M32-DEV evidence

Command executed by the pinned evidence workflow:

```bash
python -m benchmarks.m32_dev.evaluate
```

Result:

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

Solvable families with 20 cases each reached 1.0 task admission, 1.0 program admission and 1.0 strict execution:

- RU
- EN
- mixed-language
- history
- documents
- composition
- counterfactual

Conflict cases admitted their task while authority controls prevented unsafe durable promotion. Adversarial cases are negative/fail-closed cases and are not counted as solvable strict cases.

### Gate comparison

| Gate | Target | Result |
|---|---:|---:|
| Task admission | >= 95% | **100%** |
| Valid provenance | 100% | **100%** |
| Program admission on solvable DEV | >= 90% | **100%** |
| E2E strict on solvable DEV | >= 80% | **100%** |
| Unsafe authority promotions | 0 | **0** |

These numbers validate the architecture under deterministic correct proposals. They do not measure the quality of an actual LLM/Ollama model.

## M32-META freeze

The independent META generator was sealed before any integrated META evaluation.

```text
schema                            nexus.m32.meta.freeze.v1
benchmark                         M32-META
seed                              32991
case_count                        240
generator_sha256                  62a01b4c236818878664f7ca044b16028df25f269c74c3c7f1873cea2000854b
implementation_commit             6dd69420c4ea20ec64da38f7056c39d543216b77
sealed_before_first_evaluation    true
test_open_count                   0
ftx1_status                       CONSUMED_FTX1
ftx1_used_as_clean_oos            false
ftx2_authored                     false
```

M32-META remains available as an internal first-open development generalization gate. It is not FTX2.

## Regression evidence

Pinned Linux evidence workflow:

```text
pytest tests/m32 -q
39 passed in 1.63s

pytest tests/crc_r1 tests/hard_oos_f tests/hard_oos_f2 tests/crc_meta_g -q
153 passed in 4.02s
```

Independent Windows PR workflow on the later CI-only head also passed:

```text
pytest tests/m32 -q
39 passed in 2.53s

pytest tests/crc_r1 tests/hard_oos_f tests/hard_oos_f2 tests/crc_meta_g -q
153 passed in 5.12s

python -m compileall src benchmarks
PASS
```

## Frozen R1 non-regression

The evidence workflow fetched the original frozen runtime and executed:

```bash
git diff --exit-code fded8bd46777b2e868620b4c85d60c5c375b5ec1 -- \
  src/nexus_gllm/unified_v3/cognitive/conversational_reasoner.py
```

Result: **no diff**.

Current R1 source SHA-256:

`5bfa2696b8525c27fedcef1febb496f119b8410657aaf2518b21633f29be2d49`

Therefore M32 adds `ConversationalReasonerR2` rather than rewriting the FTX1-consumed R1 path.

## Scientific boundary

What is demonstrated:

1. Multi-source prompt/history/document provenance can be validated fail-closed.
2. User/document assertions can enter a transient reasoning view without silently becoming durable verified truth.
3. Typed task and program proposals can be admitted or rejected before execution.
4. The existing CRC reasoning stack can execute admitted M32 programs end-to-end.
5. Existing CRC-R1/HARD-OOS/META-G regressions remain green.

What is **not** yet demonstrated:

1. A real neural model reaches 95% task admission or 90% program admission.
2. Broad free-form RU/EN semantic extraction is solved in the wild.
3. M32 generalizes to a new untouched blind benchmark.
4. FTX2 performance is known.

## Next scientific gate

Before authoring/opening FTX2, run **M32.1 Neural Proposal Quality** with a concrete model artifact and verified digest:

```text
pinned neural model
        ↓
M32-DEV neural proposal evaluation
        ↓
sealed M32-META first-open evaluation
        ↓
architecture + thresholds freeze
        ↓
author and seal a new untouched FTX2
        ↓
one-shot FTX2
```

No FTX1 examples may be used to improve M32.1 or FTX2.
