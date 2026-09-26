# NEXUS R1.3-X cognitive core and Russian dialogue audit — 2026-09-26

## Executive result

The current R1.3-X deep-training branch has a useful authority/governance core and improved capability routing, but it is **not yet a complete autonomous cognitive Russian-language conversational system**.

The fresh HARD-5 routing score (85/90 = 94.44%) measures capability classification/routing. It must not be interpreted as 94.44% conversational Russian or full cognitive-core quality.

## What is genuinely working

### Authority/governance core

Direct execution of the current `r13x.py` logic passed the following five diagnostics:

1. exact verified arithmetic overrides a high-confidence neural proposal;
2. equal-authority contradiction causes abstention;
3. high-uncertainty low-authority proposal causes abstention;
4. memory-supported proposal overrides a neural proposal;
5. direct evidence overrides a merely causal-consistent proposal.

Result: **5/5**.

The core authority order is:

`EXACT_VERIFIED > DIRECT_EVIDENCE > CAUSAL_CONSISTENT > MEMORY_SUPPORTED > NEURAL_PROPOSAL > SURFACE_GUESS`.

### Context revision

The current R7.44 context adapter correctly retains the latest value per relation/object key in a structured event stream.

Diagnostic example:

- status(order)=created
- status(order)=paid
- status(order)=cancelled

Result: active context becomes `status(order)=cancelled`, while independent facts such as city remain available.

## Russian understanding diagnostic

The currently active `R72LanguageExpert` uses one narrow regular expression:

`<receiver> получил от <source> <object>`.

Ten Russian surface variants were tested.

Recognized:

- `Борис получил от Анны ключ.`
- `Петя получил от Ольги посылку.`

Not recognized:

- `Мария получила от Ивана книгу.`
- `Анна передала Борису ключ.`
- `Ключ Борису дала Анна.`
- `От Анны Борис получил ключ.`
- `Борис вчера получил от Анны красный ключ.`
- `Борис получил ключ от Анны.`
- `Борису Анна передала ключ.`
- `Скажи по-русски, что Анна передала Борису ключ.`

Result: **2/10** surface forms recognized.

This is pattern matching, not broad Russian semantic understanding.

## End-to-end Russian answer diagnostic

Five ordinary Russian queries were sent through the current active MoE behavior without injected `expert_answers`:

1. `Привет! Расскажи, что ты умеешь.`
2. `Почему небо голубое?`
3. `Мария получила от Ивана книгу. Что произошло?`
4. `Борис получил от Анны ключ. Что произошло?`
5. `Запомни: кодовое слово Север. Какое кодовое слово?`

Routing selected the language/hypothesis path, but no expert produced a natural-language answer candidate.

Result: **0/5 leading answers**.

Even when R72 extracted the fact from case 4, the runtime had no renderer that converted the structured fact into a Russian response.

## Missing conversational layer

The architecture document mentions a Russian renderer, but no standalone Russian renderer/decoder is present in the current R1.3-X implementation.

The active language component is a narrow semantic extractor rather than a generative dialogue model.

Therefore the branch currently cannot reliably:

- hold free-form Russian conversation;
- explain an answer naturally;
- answer open questions such as `Почему...`;
- paraphrase arbitrary Russian text;
- preserve dialogue context across free-form turns;
- render structured proof/memory/world-state results into fluent Russian.

## Cognitive-core integration gaps

### Historical organs remain SHADOW in default registry

The default registry keeps the following important experts in SHADOW mode:

- R7.6 semantic memory;
- R7.8 formal;
- R7.10 proof;
- R7.14 morphology;
- V10 procedural;
- Unified R1.3 historical authority;
- V30 procedural.

Thus the active runtime does not currently execute those capabilities end-to-end.

### Unified R1.3 itself is still shadow-only

`src/nexus_gllm/unified_v3/moe/experts/unified_r13.py` is a `ShadowAdapter` that emits no answer and uncertainty 1.0.

Therefore R1.3-X is presently an augmentation/reconstruction line around the historical architecture, not a mounted execution of the historical R1.3 brain.

### Semantic memory is not active

`r76_semantic_memory.py` is also a `ShadowAdapter`.

The root R1.3-X governor accepts proposals marked `MEMORY_SUPPORTED`, but there is no active autonomous semantic-memory expert producing them in the default MoE runtime.

### Formal/proof/morphology adapters are shadow-only

`r78_formal.py`, `r710_proof.py`, and `r714_morpholex.py` in the default adapter layer are shadow stubs.

Exact historical expert loaders exist in `exact_experts.py`, but they are not wired into the active default MoE registry/runtime here.

### Unified V3 cognitive bridge is incomplete in this branch

`nexus_gllm/r13x_unified_v3.py` imports:

- `unified_v3.contracts`
- `unified_v3.counterfactual`
- `unified_v3.epistemic`

Those modules are not present in the current branch tree. Only `src/nexus_gllm/unified_v3/moe/*` exists.

Therefore the advertised counterfactual/world/epistemic adapter cannot be treated as a verified working end-to-end cognitive runtime in this branch.

## Test caveat

`tests/test_r13x_moe_bridge.py` supplies `metadata[\"expert_answers\"]` manually:

`r7l=A, r72=A, r718=B, v3=A`.

That validates governance/plumbing but not autonomous cognition or Russian answering.

## Interpretation of HARD-5 94.44%

HARD-5 is valuable evidence that the new semantic/hybrid router classifies capability intent well on its fresh routing stress set.

It does **not** establish:

- 94.44% Russian comprehension;
- 94.44% conversational quality;
- autonomous long-term memory;
- autonomous formal reasoning;
- autonomous world-model reasoning;
- complete cognitive-core integration.

## Current readiness assessment

- authority/governance: **working**
- exact verification shell: **working**
- structured context revision: **working**
- capability routing: **strong on fresh HARD-5**
- Russian semantic extraction: **narrow / inadequate**
- Russian natural-language generation: **missing**
- free-form dialogue: **not operational**
- semantic memory: **not active**
- formal/proof/morphology historical experts: **not active in default runtime**
- counterfactual/world/epistemic bridge: **source-incomplete on this branch**
- historical Unified R1.3 runtime: **not mounted**

## Next engineering milestone

Before any claim of a Russian cognitive NEXUS, R1.3-X needs a dedicated **Cognitive Russian Runtime**:

1. activate exact R7.6/R7.8/R7.10/R7.14 experts when verified artifacts are mounted;
2. implement a persistent dialogue/session memory bus;
3. add Russian semantic parsing beyond one regex pattern;
4. add a Russian answer renderer/decoder that consumes proof, memory, evidence, world and causal outputs;
5. restore/fix counterfactual + epistemic + world contracts;
6. run multi-turn Russian dialogue tests with no injected expert answers;
7. freeze a new dialogue benchmark before tuning.

