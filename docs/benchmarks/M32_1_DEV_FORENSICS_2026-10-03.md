# M32.1 DEV Forensics — 2026-10-03

## Scientific role

M32.1 is the real-neural ingress/proposal-quality experiment. It is not the CRC cognitive-loop experiment and cannot establish AGI/transfer by itself.

`M32-META` remains sealed. `FTX2` remains unauthored.

## Reconstructed DEV lineage

### DEV-v4 grounded ontology

Hypothesis: a small model fails because NEXUS relation/program ontology and source offset expectations are implicit.

Intervention:
- explain relation/operator semantics in the system contract;
- expose whole-source span hints;
- explain QUERY_RELATION, transitive/composition/counterfactual program forms.

Important result from later history: explanation alone did not close neural proposal quality.

### DEV-v4 grounded few-shot

Hypothesis: demonstrations can teach exact grounding.

Intervention:
- grounded transitive/composition/counterfactual examples.

But the model was still asked to emit recursive ProgramNode AST and character offsets. Therefore this did not isolate semantic grounding from syntax/provenance arithmetic.

### DEV-v5 exact quality

Hypothesis: admission/E2E alone hide proposal errors.

Intervention:
- add `semantic_exact_expected`;
- add `task_exact_expected`;
- add `program_shape_exact_solvable`;
- add negative rejection rate;
- target observed source-local/counterfactual/prompt failures.

Critical branch-drift finding: these exact-quality metrics were later lost from the branch that became the V7 pinned-schema line. Current V7 `evaluate_dev.py` reports the older coarse v1 schema. This must be restored as measurement instrumentation after the current 1:1 V7-comparable run; scorer changes must not be conflated with model-quality changes.

### DEV-v5 typed neural IR compiler

Real-run diagnosis recorded in PR history: Qwen3.5-0.8B could emit ontology tokens but was unreliable at recursive NEXUS AST construction (`opcode:null`, recursive AST loops/truncation).

Intervention:
- neural model emits shallow `semantic_atoms + task + program_recipe`;
- deterministic code compiles ProgramNode;
- deterministic code supplies full-source provenance;
- unknown recipe/source IDs fail closed.

This is a valid architecture reduction: semantic choice remains neural; mechanical structure/provenance arithmetic is deterministic.

### DEV-v6 capacity-gate prompt

Hypothesis: remaining errors might be capacity/prompt limits.

Intervention:
- more targeted prompt/few-shot cases and source lengths.

Actual evidence status: NO clean capacity verdict. The PR contract run failed before real-model qualification because two old/new prompt-contract assertions were incompatible (`13 passed, 2 failed`). Therefore it is invalid to cite this branch as proof that 0.8B capacity is insufficient.

### DEV-v6 schema-constrained shallow IR

Hypothesis: constrain generated structure at decoding time.

Intervention:
- JSON schema for shallow typed IR;
- constrained source IDs, task opcodes, recipe kinds/cardinality.

Later forensic finding: the llama.cpp request wrapper was wrong for the pinned commit, so the intended schema was not actually enforced.

### DEV-v7 pinned schema wire

Intervention:
- exact pinned llama.cpp wrapper `response_format.json_schema.schema`.

Real-model result:
- 180 cases / 9 unique deterministic neural calls;
- ingress acceptance = 1.0;
- provenance validity = 1.0;
- task admission = 0.0;
- program admission on solvable = 0.0;
- E2E strict solvable = 0.0;
- unsafe authority promotions = 0;
- unexpected adversarial admissions = 20.

Raw completion diagnosis:
- JSON/schema form is now valid;
- model frequently copies schema/metavocabulary into semantic slots (`query_relation`, `source_entity`, `source_kind`, etc.);
- task/program_recipe are usually null;
- therefore the active blocker is grounded value mapping, not JSON syntax or AST construction.

Verdict: `M32.1 DEV REAL NEURAL QUALITY = RED`.

## Current controlled follow-up

Branch: `m32-1-neural-dev-grounded-typed-fewshot`

Base: exact V7 head `f8c928ed68d45a07f279aab9de7488fde20856f9`.

Hypothesis under test:

> With the exact schema really enforced and recursive AST/provenance arithmetic already removed, grounded demonstrations expressed in the same shallow typed IR may teach the 0.8B model to map visible source values into semantic/task/program slots instead of copying schema metavocabulary.

This is a combination not isolated by the earlier branches:

- grounded few-shot existed with recursive AST/offset burden;
- shallow typed IR existed without grounded shallow demonstrations;
- enforced schema existed without grounded shallow demonstrations.

TDD evidence:
- RED commit `0efa3490fe5d07c263b7e2d430680cf48be144af`;
- M32.1 contract: `2 failed, 12 passed`;
- failures exactly: zero assistant demonstrations and missing explicit schema-label/source-value separation.

Implementation commit:
- `b02885218b5c1d643b2c62627c308dfefccc0ff4`;
- adds three shallow typed demonstrations: transitive, composition, counterfactual_transitive;
- adds explicit anti-meta-copy instruction;
- does not change model bytes, model SHA, llama.cpp pin, typed decoder/compiler, benchmark cases, coarse scorer, META or FTX state.

Unit/contract status at time of this ledger update:
- M32.1 contract GREEN on implementation commit;
- full generic CI GREEN on implementation commit;
- real neural DEV run launched on the same exact GGUF/pinned llama.cpp execution path.

The real neural result, not the unit tests, determines whether the hypothesis survives.

## Evidence discipline

Do not state any of the following until supported by the corresponding evidence:

- `M32.1 GREEN` from contract tests alone;
- `0.8B capacity failure` from the aborted capacity-gate PR;
- `CRC improved` from any M32.1 result;
- `TRANSFER CONFIRMED` from DEV data;
- any META or FTX verdict before first-open execution.
