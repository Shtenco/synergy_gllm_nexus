# M32 — Generalized Semantic + Task Ingress

Date: 2026-10-01
Base: `fded8bd46777b2e868620b4c85d60c5c375b5ec1` (frozen CRC-R1)
Status: design/specification

## 1. Purpose

M32 exists because the first and only clean FTX1 opening showed an end-to-end ingress failure: the frozen default task parser admitted 0/2400 blind prompts, so every case returned `UNRESOLVED` before program synthesis or downstream CRC reasoning.

FTX1 is consumed and must never be used as clean OOS again. M32 development may use fresh DEV/diagnostic corpora and explicitly labelled consumed FTX1 diagnostics, but no M32 success claim may be based on FTX1 as untouched OOS. A new sealed FTX2 is required for the next clean claim.

The target flow is:

```text
free RU/EN text
+ dialogue history
+ documents
+ multilingual context
        ↓
proposal-only generalized ingress
        ↓
span/provenance admission
        ↓
semantic authority separation
        ↓
transient reasoning context
+ typed TaskProgram
+ executable Program AST hypothesis
        ↓
existing CRC reasoning organs
```

## 2. What the frozen code already has

CRC-R1 already provides strong boundaries that M32 should preserve rather than replace:

- `LanguageCortexPort` + `LanguageProposalGate`: proposal-only semantic atoms with exact source-span hashing.
- `TaskCortexPort` + `TaskProposalGate`: proposal-only typed `TaskProgram`.
- `SemanticCommitGate`: distinguishes `PROPOSED`, `ASSERTED_CONTEXT`, `VERIFIED`, `REJECTED`.
- `OllamaLanguageCortexBackend` and `OllamaTaskCortexBackend`: model-backed proposal adapters with verified model digest, JSON output and source offsets.
- `ProgramNode`, `ProgramCompiler`, `ProgramSynthesisCortex`, `HigherOrderExecutor`: typed program representation and execution.
- `CognitiveLoopR1`: downstream deliberation.

M32 therefore should not give a language model direct truth, commit, execution or action authority.

## 3. The three actual frozen ingress gaps

### Gap A — task admission

`ConversationalReasonerR1` defaults to `ControlledTaskBackend`, which recognizes only two narrow Russian relation-query forms. General free text is rejected before reasoning.

### Gap B — asserted context is not available to reasoning

`SemanticCommitGate` correctly refuses to promote model/user assertions to `VERIFIED`, but `ConversationShellR1.world` contains only verified facts. `ASSERTED_CONTEXT` is retained as metadata/context, not as structured atoms in the world passed to the executor.

That is safe for authority, but too restrictive for hypothetical/benchmark/dialogue reasoning. The system needs a transient reasoning view that can use asserted context while preserving its lower epistemic status.

### Gap C — no evidence means no executable program

`ProgramSynthesisCortex.synthesize()` returns `selected=None` when `evidence` is empty. `ConversationalReasonerR1.answer()` normally supplies no program evidence, so a newly admitted task can still stop before CRC execution.

M32 must provide an admitted executable program hypothesis (or grounded demonstrations/evidence sufficient for synthesis) without target/gold injection.

## 4. Selected approach

Build a generalized multi-source ingress orchestrator with neural proposal adapters and strict deterministic gates.

One ingress request contains prompt, history and documents as separately addressable sources. A model proposes semantic atoms, task and optional program AST, each with source references. NEXUS recomputes all hashes, validates types and structure, assigns authority, builds a transient reasoning world, and only then invokes CRC.

The model remains proposal-only and has zero truth/commit/execution authority.

## 5. New contracts

### SourceEnvelope

Each source is immutable and independently hash-addressed:

```text
source_id
source_kind: PROMPT | HISTORY | DOCUMENT
ordinal
text
sha256
trust_class
```

### GroundedSpanRef

```text
source_id
start
end
sha256
```

NEXUS recomputes the digest from the original source text. Invalid source IDs, bounds or hashes fail closed.

### GeneralizedSemanticProposal

Semantic atoms + grounded source spans. Model may propose; authority is assigned by NEXUS.

### GeneralizedTaskProposal

```text
opcode
operator_id
arguments
confidence
supporting_spans
```

### ProgramProposal

Proposal-only typed `ProgramNode` AST + provenance + confidence. AST depth/node count/operator references are bounded and validated.

## 6. GeneralizedIngressR1

```text
GeneralizedIngressR1.parse(request)
    1. validate SourceEnvelopes
    2. invoke GeneralizedIngressBackend
    3. validate semantic spans
    4. validate task proposal
    5. validate program proposal
    6. assign semantic authority classes from source origin
    7. return immutable GeneralizedIngressResult
```

Backend protocol:

```text
GeneralizedIngressBackend.propose(request) -> GeneralizedIngressProposal
```

## 7. Neural backend

`OllamaGeneralizedIngressBackend` extends the existing verified-model pattern.

Requirements:

- verified 64-char model digest mandatory;
- temperature = 0;
- strict JSON response;
- explicit source IDs;
- source-local offsets;
- extraction only, never answer generation;
- no gold/scorer fields;
- backend exceptions fail closed.

The backend may propose semantic atoms, task and program AST in one call so cross-source references remain coherent.

## 8. Authority model

Durable `ConversationShellR1.world` remains verified-only.

M32 adds immutable transient `ReasoningContextView`:

```text
fact
status: ASSERTED_CONTEXT | VERIFIED
source_ids
provenance_ids
```

Reasoning uses:

```text
execution_world = verified_world ∪ admitted_asserted_context
```

but asserted facts are never silently promoted into durable verified world.

## 9. Program admission and selection

Add `ProgramProposalGate`.

Checks:

- known AST node kinds;
- bounded depth/node count;
- safe identifiers;
- operator references grounded in task/context or declared structural built-ins;
- no side-effect/action nodes;
- confidence threshold;
- provenance exists.

Selection order:

1. admitted generalized program proposal;
2. existing `ProgramSynthesisCortex` using grounded demonstration/evidence;
3. unresolved.

No target answer may participate in selection.

## 10. ConversationalReasonerR2

Do not mutate frozen R1 semantics in place.

```text
request = GeneralizedIngressRequest(prompt, history, documents)
ingress = generalized_ingress.parse(request)
if no admitted task: UNRESOLVED
context = build_reasoning_context(ingress)
program = admitted_program or synthesize(context, task, ingress.program_evidence)
if no program: UNRESOLVED
decision = CognitiveLoopR1.deliberate(...)
result = epistemic projection + provenance-aware surface
```

Frozen `ConversationalReasonerR1` remains unchanged for FTX1 reproducibility.

## 11. Development benchmark policy

- FTX1 = `CONSUMED_FTX1` diagnostic only.
- Create fresh `M32-DEV` with RU/EN/mixed language/history/documents/composition/counterfactual/conflict/adversarial gate cases.
- Create separate frozen `M32-META` generator/seed before first integrated meta run.
- Author and seal FTX2 only after M32 architecture/thresholds are frozen.

## 12. Acceptance gates

Engineering gates:

```text
unit/integration tests                  PASS
existing CRC-R1 tests                  no regressions
malformed proposal fail-closed         100%
authority escalation violations        0
source-span integrity violations       0
R1 frozen path modified                0
```

Initial DEV targets:

```text
task admission                         >= 95%
span/provenance validity               = 100% for admitted proposals
program admission on solvable DEV      >= 90%
end-to-end strict on solvable DEV      >= 80%
unsafe authority promotions            = 0
```

Fixture/mock transport tests prove architecture/contracts only, not neural quality.

## 13. Expected files

```text
src/nexus_gllm/unified_v3/cognitive/generalized_ingress.py
src/nexus_gllm/unified_v3/cognitive/generalized_ingress_ollama.py
src/nexus_gllm/unified_v3/cognitive/reasoning_context.py
src/nexus_gllm/unified_v3/cognitive/program_proposal.py
src/nexus_gllm/unified_v3/cognitive/conversational_reasoner_r2.py
benchmarks/m32_dev/*
benchmarks/m32_meta/*
tests/m32/*
```

## 14. Scientific boundary

M32 is an engineering milestone. Generalization remains unproven until frozen M32 is tested once against a newly sealed FTX2.
