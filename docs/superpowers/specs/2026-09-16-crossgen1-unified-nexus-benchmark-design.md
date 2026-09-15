# NEXUS CROSSGEN-1 — Unified Cross-Generation Benchmark

**Date:** 2026-09-16  
**Status:** user-approved, frozen before cross-generation reruns  
**Purpose:** compare all discoverable NEXUS generations without treating incompatible native benchmark percentages as a single leaderboard.

## 1. Scientific rule
Each NEXUS release receives two distinct evidence layers:
1. **Native evidence** — its own frozen/sealed benchmark, reproduced when physically runnable.
2. **CrossGen-1 evidence** — common post-freeze tasks executed only on versions for which a compatible runtime adapter can be built without changing model logic.

A missing runtime is `NR` (not rerunnable), never score 0. Historical scores do not become CrossGen scores.

## 2. Evidence grades
- `E3 fresh-rerun`: physical runtime/checkpoint and current CrossGen/native rerun completed.
- `E2 runnable-native`: current native self-test/runtime completed, but no valid CrossGen adapter.
- `E1 physical-evidence`: release/result/checkpoint exists, but current runtime incomplete or incompatible.
- `E0 historical-only`: report/ledger claim exists without enough physical runtime to rerun.

## 3. CROSSGEN-1 private suite
The private suite is generated after all compared releases are frozen. It contains **12,000 tasks**, six balanced panels of 2,000 tasks:
- `RU_LANG`: Russian paraphrase, negation, morphology, order changes, lexical substitutions.
- `GRAPH`: exact SUBJECT→OPERATOR→OBJECT, inverse roles, multi-clause distractors, multi-word arguments.
- `REASON`: arithmetic, logic, temporal/causal composition, proof-like micro tasks.
- `CONTEXT`: anaphora, multi-turn state, conflict/update, delayed recall.
- `FAR_TRANSFER`: nonce micro-world learning, 1–4 hop deduction, RU↔EN cross-language transfer.
- `OOD_OVERFIT`: paired ID/OOD templates, new entities/domains/lengths/distractors and dynamic surface rewrites.

No task text is used for model selection, training or adapter-specific logic.

## 4. Far-transfer metrics
For hop distance d=1..4 record `Accuracy_d`.

`FTI = sum(d * Accuracy_d) / sum(d)`

Cross-language transfer:

`XLT = Accuracy_cross_language / max(Accuracy_same_language, eps)`

Memory-capable runtimes additionally report retention at delay 1/10/100 turns when the native interface supports persistent state without modification.

## 5. Overfitting metrics
Paired ID/OOD tasks measure:
- `G_surface = Acc_ID - Acc_surfaceOOD`
- `G_template = Acc_ID - Acc_templateOOD`
- `G_entity = Acc_ID - Acc_entityOOD`
- `G_domain = Acc_ID - Acc_domainOOD`
- `G_length = Acc_ID - Acc_lengthOOD`

Diagnostic overfit index:

`OI = 1 - Acc_OODmean / max(Acc_ID, eps)`

The component gaps are always reported alongside OI.

## 6. Public reference layer
Public benchmarks are secondary reference panels, not contamination-safe primary scores. When a compatible runtime exists, adapters may run subsets of:
- MERA / Russian language and reasoning tasks;
- RussianSuperGLUE;
- MultiLoKo Russian/local knowledge transfer;
- CLUTRR relational induction;
- SCAN compositional/length transfer;
- SimpleQA/BrowseComp/DeepResearch-style research tasks for Ω-1.6 research mode.

Published benchmark exposure is disclosed separately from the private CrossGen score.

## 7. Adapter contract
A version adapter exposes only capabilities the historical runtime already had:

```python
class NexusAdapter:
    id: str
    evidence_grade: str
    capabilities: set[str]
    def reset(self) -> None: ...
    def answer(self, task: CrossGenTask) -> AdapterResult: ...
```

Adapters may translate the common task into a native input schema but may not add reasoning, lexical rules, web search, hidden teacher inference or external LLMs unless that capability was part of the frozen historical runtime and is reported in a separate augmented mode.

## 8. Core vs augmented mode
Teacher/ensemble generations are reported separately:
- `NATIVE_CORE`: external teachers disabled/unavailable.
- `HISTORICAL_AUGMENTED`: only exact frozen teacher traces/artifacts that belonged to that release.

Live modern external LLMs may not be substituted for missing historical teachers.

## 9. Web policy
Core CrossGen runs are `WEB=OFF` for every version, including Ω-1.6. Research capability receives a separate research panel so web access cannot leak answers to the general benchmark.

## 10. Scoring
No single universal leaderboard score is authoritative. The Capability Atlas reports:
- RU language accuracy/coverage;
- graph exact triple;
- reasoning accuracy;
- context/state accuracy;
- far-transfer FTI;
- cross-language XLT;
- OOD accuracy and overfit gaps/OI;
- open-set/abstention precision/recall when supported;
- evidence/research metrics when supported;
- latency and failure rate;
- evidence grade.

A convenience macro-average may be printed only across common panels jointly executed by the compared pair, clearly labeled `COMMON-PANEL MACRO`, never as global intelligence.

## 11. Statistical comparison
For two versions evaluated on the same binary-scored task IDs:
- paired bootstrap 95% confidence interval for score difference;
- McNemar test when sufficient discordant pairs exist;
- effect size / absolute percentage-point difference;
- common answered-task count and coverage.

A numerically higher result is not called a verified improvement when uncertainty/paired evidence does not support it.

## 12. Artifact discovery
Search scope:
- all accessible Shtenco GitHub repositories and NEXUS-related branches/files;
- Google Drive NEXUS folders, freeze ZIPs and benchmark/result archives;
- existing `/mnt/data` releases already downloaded from those sources.

Duplicate releases are content-hash clustered. The report records source URI/path, SHA-256, runtime status and discovered version identity.

## 13. Reproducibility
Before executing any CrossGen adapter, freeze:
- generator source SHA-256;
- suite JSONL SHA-256;
- task count and panel balance;
- benchmark seed;
- normalization/scoring version;
- current Ω repository head/checkpoint hashes;
- artifact inventory hash.

CrossGen task content is not changed after the first evaluated runtime.

## 14. Limitations
CROSSGEN-1 is an internal engineering benchmark. It does not prove AGI or unrestricted language intelligence. Structured specialists may legitimately have low or unsupported coverage on free-language panels; this is reported as capability scope rather than silently reinterpreted as general failure.