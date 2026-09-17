# NEXUS Unified v3 P0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a falsifiable Unified v3 P0 vertical slice that converts controlled surface inputs into a text-quarantined Semantic IR, induces unknown operator behavior and task programs, executes multi-step reasoning, preserves epistemic uncertainty, audits generalization invariance, and renders a faithful Russian answer.

**Architecture:** New code lives only in `src/nexus_gllm/unified_v3/`; Unified v2 remains immutable and available only behind replaceable donor adapters. Raw text terminates at the surface boundary. Every downstream component consumes typed semantic structures, and the executor accepts only `WorldHypothesis + RuleProgram + TaskProgram`.

**Tech Stack:** Python >=3.11, stdlib dataclasses/enums/typing/hashlib/re, pytest >=8. No new runtime dependency is required for P0.

**Spec:** `docs/superpowers/specs/2026-09-17-nexus-unified-v3-generalization-first-design.md`

## Global Constraints

- All v3 production code lives under `src/nexus_gllm/unified_v3/`.
- Unified v2 source is immutable for this feature.
- Downstream reasoning contracts MUST NOT expose raw prompt/history/document text.
- No FTX1 BLIND corpus, gold, generator, renderer IDs, pair IDs, split IDs, track IDs, answer indices, or proof paths may be read by v3 code.
- Parser/rule/task components propose semantics; only the epistemic path licenses assertion.
- P0 must fail closed on material ambiguity.
- Every behavior change starts with a failing pytest test.
- Every derived fact carries a derivation/provenance ledger.
- P0 must include negative controls so invariance cannot pass by collapsing every input to the same representation.

---

## File map

- `src/nexus_gllm/unified_v3/contracts.py` — immutable public dataclasses/enums shared by all P0 modules.
- `src/nexus_gllm/unified_v3/semantic_ir.py` — normalization, semantic fingerprints and raw-text quarantine checks.
- `src/nexus_gllm/unified_v3/surface.py` — controlled P0 surface adapter; the only module allowed to consume raw strings.
- `src/nexus_gllm/unified_v3/role_binding.py` — role normalization independent of active/passive wording.
- `src/nexus_gllm/unified_v3/world.py` — world hypotheses, fact identity and revision-safe world construction.
- `src/nexus_gllm/unified_v3/rule_induction.py` — anonymous operator hypothesis induction from demonstrations.
- `src/nexus_gllm/unified_v3/task_induction.py` — task-program induction from structured examples.
- `src/nexus_gllm/unified_v3/executor.py` — bounded compositional execution with derivation ledger.
- `src/nexus_gllm/unified_v3/epistemic.py` — PROVED/DISPROVED/UNRESOLVED/CONFLICTED resolution.
- `src/nexus_gllm/unified_v3/generalization.py` — invariance/intervention audits over semantic structures.
- `src/nexus_gllm/unified_v3/renderer.py` — Russian realization from structured epistemic result only.
- `src/nexus_gllm/unified_v3/runtime.py` — P0 orchestration and structured trace.
- `tests/unified_v3/*` — behavior-first tests for each boundary plus the end-to-end P0 slice.

---

### Task 1: Typed semantic contracts and hard raw-text quarantine

**Files:**
- Create: `src/nexus_gllm/unified_v3/__init__.py`
- Create: `src/nexus_gllm/unified_v3/contracts.py`
- Create: `src/nexus_gllm/unified_v3/semantic_ir.py`
- Test: `tests/unified_v3/test_semantic_ir.py`

**Interfaces:**
- Produces: `Entity`, `OperatorSymbol`, `SemanticAtom`, `SemanticObservation`, `WorldFact`, `WorldHypothesis`, `RuleHypothesis`, `RuleProgram`, `TaskProgram`, `DerivedFact`, `ExecutionResult`, `EpistemicState`, `EpistemicResult`, `GeneralizationAudit`, `TraceEvent`, `V3Response`.
- Produces: `semantic_fingerprint(observation: SemanticObservation) -> str`.
- Produces: `assert_text_quarantined(value: object) -> None` which recursively rejects reasoning-facing dataclasses containing forbidden raw-text field names.

- [ ] **Step 1: Write failing contract/quarantine tests**

```python
from dataclasses import dataclass
import pytest

from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, SemanticAtom, SemanticObservation
from nexus_gllm.unified_v3.semantic_ir import assert_text_quarantined, semantic_fingerprint


def test_semantic_fingerprint_ignores_surface_aliases_but_not_semantic_roles():
    a = SemanticObservation(atoms=(SemanticAtom(OperatorSymbol("op:x", 2), (Entity("e:a"), Entity("e:b"))),))
    b = SemanticObservation(atoms=(SemanticAtom(OperatorSymbol("op:x", 2), (Entity("e:a"), Entity("e:b"))),))
    c = SemanticObservation(atoms=(SemanticAtom(OperatorSymbol("op:x", 2), (Entity("e:b"), Entity("e:a"))),))
    assert semantic_fingerprint(a) == semantic_fingerprint(b)
    assert semantic_fingerprint(a) != semantic_fingerprint(c)


def test_reasoning_contract_rejects_raw_text_field():
    @dataclass(frozen=True)
    class BadReasoningObject:
        prompt: str
    with pytest.raises(ValueError, match="raw text field"):
        assert_text_quarantined(BadReasoningObject("leak"))
```

- [ ] **Step 2: Run RED**

Run: `pytest tests/unified_v3/test_semantic_ir.py -q`
Expected: import/collection failure because `unified_v3` contracts do not exist.

- [ ] **Step 3: Implement minimal immutable contracts and canonical fingerprint**

Use frozen dataclasses and enums. `SemanticAtom.arguments` is a tuple of entity/scalar references; operator identity is anonymous/local. `semantic_fingerprint` serializes canonical semantic content only, never aliases or raw text. `assert_text_quarantined` recursively checks dataclass field names against `{prompt,text,text_ru,raw_text,history,document,documents,renderer_id,split_id,track_id}`.

- [ ] **Step 4: Run GREEN**

Run: `pytest tests/unified_v3/test_semantic_ir.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/nexus_gllm/unified_v3 tests/unified_v3/test_semantic_ir.py
git commit -m "feat(v3): add semantic contracts and quarantine"
```

---

### Task 2: Surface adapter and role-invariant semantic normalization

**Files:**
- Create: `src/nexus_gllm/unified_v3/surface.py`
- Create: `src/nexus_gllm/unified_v3/role_binding.py`
- Test: `tests/unified_v3/test_surface_invariance.py`

**Interfaces:**
- Consumes: contracts from Task 1.
- Produces: `SurfaceRequest` in `surface.py` as the sole raw-text boundary type.
- Produces: `ControlledSurfaceAdapter.parse(request: SurfaceRequest) -> SemanticObservation`.
- Produces: `RoleBinder.bind(observation: SemanticObservation) -> SemanticObservation`.

- [ ] **Step 1: Write RED tests for three Russian renderings and a negative control**

```python
from nexus_gllm.unified_v3.semantic_ir import semantic_fingerprint
from nexus_gllm.unified_v3.surface import ControlledSurfaceAdapter, SurfaceRequest


def test_active_passive_and_reordered_forms_share_semantics():
    adapter = ControlledSurfaceAdapter()
    forms = [
        "Анна передала ключ Борису.",
        "Ключ был передан Борису Анной.",
        "Борис получил от Анны ключ.",
    ]
    fps = {semantic_fingerprint(adapter.parse(SurfaceRequest(text=x))) for x in forms}
    assert len(fps) == 1


def test_true_role_swap_changes_semantics():
    adapter = ControlledSurfaceAdapter()
    a = adapter.parse(SurfaceRequest(text="Анна передала ключ Борису."))
    b = adapter.parse(SurfaceRequest(text="Борис передал ключ Анне."))
    assert semantic_fingerprint(a) != semantic_fingerprint(b)
```

- [ ] **Step 2: Run RED**

Run: `pytest tests/unified_v3/test_surface_invariance.py -q`
Expected: FAIL because surface adapter is absent.

- [ ] **Step 3: Implement controlled surface boundary**

P0 uses a deliberately narrow deterministic parser for transfer-style Russian fixtures plus a structured constructor for tests. It maps lexical variants to generic semantic role structure. The parser may use regex internally, but output contains no raw strings beyond normalized entity IDs and scalar values.

- [ ] **Step 4: Add quarantine assertion over adapter output**

The test must call `assert_text_quarantined(parsed)` for every rendering.

- [ ] **Step 5: Run GREEN**

Run: `pytest tests/unified_v3/test_surface_invariance.py tests/unified_v3/test_semantic_ir.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/nexus_gllm/unified_v3/surface.py src/nexus_gllm/unified_v3/role_binding.py tests/unified_v3/test_surface_invariance.py
git commit -m "feat(v3): add role-invariant surface boundary"
```

---

### Task 3: World hypotheses and anonymous rule induction

**Files:**
- Create: `src/nexus_gllm/unified_v3/world.py`
- Create: `src/nexus_gllm/unified_v3/rule_induction.py`
- Test: `tests/unified_v3/test_rule_induction.py`

**Interfaces:**
- Produces: `WorldInducer.from_observations(observations: tuple[SemanticObservation, ...]) -> tuple[WorldHypothesis, ...]`.
- Produces: `RuleInducer.induce(demonstrations: tuple[RuleDemonstration, ...]) -> RuleProgram`.
- `RuleDemonstration` contains only semantic facts plus expected semantic consequence/non-consequence; it contains no natural-language relation name.

- [ ] **Step 1: Write RED tests for operator rename invariance and non-transitive negative control**

```python
from nexus_gllm.unified_v3.rule_induction import RuleDemonstration, RuleInducer


def chain(op, a, b, c, positive=True):
    return RuleDemonstration.chain(operator=op, left=a, middle=b, right=c, consequence=positive)


def test_nonce_operator_rename_preserves_transitive_rule_shape():
    r1 = RuleInducer().induce((chain("op:zurit", "a", "b", "c"), chain("op:zurit", "d", "e", "f")))
    r2 = RuleInducer().induce((chain("op:kema", "a", "b", "c"), chain("op:kema", "d", "e", "f")))
    assert r1.shape_fingerprint() == r2.shape_fingerprint()


def test_negative_demonstration_blocks_transitivity_hypothesis():
    program = RuleInducer().induce((chain("op:q", "a", "b", "c", positive=False),))
    assert not program.has_property("transitive")
```

- [ ] **Step 2: Run RED**

Run: `pytest tests/unified_v3/test_rule_induction.py -q`
Expected: FAIL because induction classes are absent.

- [ ] **Step 3: Implement hypothesis scoring**

P0 candidate families are `identity/direct`, `transitive`, `symmetric`, and `blocked_nontransitive`. Score candidates by explained demonstrations, contradictions, then simplicity. Preserve a tie as multiple hypotheses rather than silently forcing one.

- [ ] **Step 4: Add entity-rename invariance test**

Generate the same demonstration structure with different entity IDs and assert equal `shape_fingerprint()`.

- [ ] **Step 5: Run GREEN**

Run: `pytest tests/unified_v3/test_rule_induction.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/nexus_gllm/unified_v3/world.py src/nexus_gllm/unified_v3/rule_induction.py tests/unified_v3/test_rule_induction.py
git commit -m "feat(v3): induce anonymous operator rules"
```

---

### Task 4: Task-program induction and text-free compositional executor

**Files:**
- Create: `src/nexus_gllm/unified_v3/task_induction.py`
- Create: `src/nexus_gllm/unified_v3/executor.py`
- Test: `tests/unified_v3/test_task_executor.py`

**Interfaces:**
- Produces: `TaskExample(input_facts, query, expected)` with semantic values only.
- Produces: `TaskInducer.induce(examples: tuple[TaskExample, ...]) -> TaskProgram`.
- Produces: `Executor.execute(world: WorldHypothesis, rules: RuleProgram, task: TaskProgram, *, max_steps: int = 5) -> ExecutionResult`.

- [ ] **Step 1: Write RED task-induction test**

Use semantic examples showing that the requested operation is a binary relation query. Assert the induced program opcode equals `QUERY_RELATION` without passing a track/task-name string.

- [ ] **Step 2: Write RED 3-step composition test**

Construct world facts `A->B`, `B->C`, `C->D` for an anonymously induced transitive operator. Query `A->D`; assert the result is true and derivation depth is 3.

- [ ] **Step 3: Write contract test proving executor rejects raw surface objects**

Call executor with `SurfaceRequest` in place of a world and assert `TypeError`. Verify public executor signature contains no `str`, `prompt`, or `text` parameter.

- [ ] **Step 4: Run RED**

Run: `pytest tests/unified_v3/test_task_executor.py -q`
Expected: FAIL because task inducer/executor are absent.

- [ ] **Step 5: Implement minimal task opcode induction and bounded forward chaining**

Use an enum-backed `TaskProgram`. Executor forward-chains derived facts up to `max_steps`, deduplicates semantic facts, stores `DerivedFact(parents, rule_id, depth)`, and never reads surface text.

- [ ] **Step 6: Add 5-step bound and blocked-rule negative tests**

A six-hop-only proof with `max_steps=5` must return unresolved/not-derived. A blocked non-transitive rule must not synthesize a transitive edge.

- [ ] **Step 7: Run GREEN**

Run: `pytest tests/unified_v3/test_task_executor.py tests/unified_v3/test_rule_induction.py -q`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/nexus_gllm/unified_v3/task_induction.py src/nexus_gllm/unified_v3/executor.py tests/unified_v3/test_task_executor.py
git commit -m "feat(v3): add task induction and compositional executor"
```

---

### Task 5: Epistemic controller and faithful Russian renderer

**Files:**
- Create: `src/nexus_gllm/unified_v3/epistemic.py`
- Create: `src/nexus_gllm/unified_v3/renderer.py`
- Test: `tests/unified_v3/test_epistemic_renderer.py`

**Interfaces:**
- Produces: `EpistemicController.resolve(results: tuple[ExecutionResult, ...]) -> EpistemicResult`.
- Produces: `RussianRenderer.render(result: EpistemicResult) -> str`.

- [ ] **Step 1: Write RED tests for all four epistemic states**

Cases: positive derivation only -> `PROVED`; explicit negative derivation only -> `DISPROVED`; neither -> `UNRESOLVED`; both -> `CONFLICTED`.

- [ ] **Step 2: Write renderer faithfulness tests**

Assert unresolved Russian output contains `Недостаточно данных`; conflicted output contains `противореч`; proved/disproved output does not fabricate an entity absent from the result payload.

- [ ] **Step 3: Run RED**

Run: `pytest tests/unified_v3/test_epistemic_renderer.py -q`
Expected: FAIL because controller/renderer are absent.

- [ ] **Step 4: Implement minimal resolver and renderer**

Renderer accepts only `EpistemicResult`; no raw request is available to it.

- [ ] **Step 5: Run GREEN**

Run: `pytest tests/unified_v3/test_epistemic_renderer.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/nexus_gllm/unified_v3/epistemic.py src/nexus_gllm/unified_v3/renderer.py tests/unified_v3/test_epistemic_renderer.py
git commit -m "feat(v3): add epistemic controller and Russian renderer"
```

---

### Task 6: Generalization Governor with invariance and intervention controls

**Files:**
- Create: `src/nexus_gllm/unified_v3/generalization.py`
- Test: `tests/unified_v3/test_generalization_governor.py`

**Interfaces:**
- Produces: `GeneralizationGovernor.audit(base: ExecutionResult, variants: tuple[ExecutionResult, ...], interventions: tuple[InterventionCheck, ...] = ()) -> GeneralizationAudit`.
- `GeneralizationAudit` exposes `stable`, `invariance_rate`, `intervention_sensitivity`, `violations`, `confidence`.

- [ ] **Step 1: Write RED invariance test**

Three semantics-preserving renderings that produce the same semantic answer must yield `stable=True` and invariance rate `1.0`.

- [ ] **Step 2: Write RED collapse detector**

Provide a declared semantic intervention expected to change the answer. If base and intervention result are equal, audit must fail even though paraphrase invariance is perfect.

- [ ] **Step 3: Run RED**

Run: `pytest tests/unified_v3/test_generalization_governor.py -q`
Expected: FAIL because governor is absent.

- [ ] **Step 4: Implement audit math**

Confidence combines invariance and intervention sensitivity; a failed expected-change intervention adds an explicit violation and prevents `stable=True`.

- [ ] **Step 5: Run GREEN**

Run: `pytest tests/unified_v3/test_generalization_governor.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/nexus_gllm/unified_v3/generalization.py tests/unified_v3/test_generalization_governor.py
git commit -m "feat(v3): add generalization governor"
```

---

### Task 7: Unified v3 P0 vertical runtime and trace

**Files:**
- Create: `src/nexus_gllm/unified_v3/runtime.py`
- Test: `tests/unified_v3/test_runtime_p0.py`

**Interfaces:**
- Produces: `UnifiedNexusV3P0.respond(request: SurfaceRequest, *, demonstrations: tuple[RuleDemonstration, ...], task_examples: tuple[TaskExample, ...], audit_variants: tuple[SurfaceRequest, ...] = ()) -> V3Response`.
- `V3Response` contains structured epistemic result, rendered Russian text, generalization audit and trace; it does not expose hidden benchmark metadata.

- [ ] **Step 1: Write RED end-to-end unseen-operator test**

Use demonstrations for nonce operator `зурит`/`op:zurit` that imply transitivity, a query requiring 2-3 rule applications, and two paraphrased surface variants. Assert `PROVED`, correct semantic answer, Russian rendering, provenance depth, and stable audit.

- [ ] **Step 2: Write RED renamed-universe twin test**

Rename all entities and the nonce operator while preserving structure. Assert identical rule-shape fingerprint, task opcode, epistemic state and generalization outcome.

- [ ] **Step 3: Write RED non-transitive universe test**

Keep a similar surface style but change demonstrations so transitivity is invalid. Assert the runtime does not derive the transitive conclusion.

- [ ] **Step 4: Run RED**

Run: `pytest tests/unified_v3/test_runtime_p0.py -q`
Expected: FAIL because runtime is absent.

- [ ] **Step 5: Implement orchestration and trace events**

Trace kinds: `surface_parse`, `bind`, `world_build`, `rule_induce`, `task_induce`, `execute`, `epistemic`, `generalization`, `render`. No trace detail may include sealed metadata.

- [ ] **Step 6: Run focused GREEN suite**

Run: `pytest tests/unified_v3 -q`
Expected: all v3 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/nexus_gllm/unified_v3/runtime.py tests/unified_v3/test_runtime_p0.py
git commit -m "feat(v3): integrate P0 generalization-first runtime"
```

---

### Task 8: Regression, anti-leak audit and P0 checkpoint report

**Files:**
- Create: `docs/results/2026-09-17-nexus-unified-v3-p0-report.md`
- Modify only if required for exports: `src/nexus_gllm/unified_v3/__init__.py`

**Interfaces:**
- Consumes complete P0.
- Produces a reproducible report with source commit, test commands and outcomes, explicit limitations, and a statement that BLIND was not accessed.

- [ ] **Step 1: Run static forbidden-field scan**

Run:

```bash
python - <<'PY'
from pathlib import Path
root = Path('src/nexus_gllm/unified_v3')
forbidden = ('renderer_id', 'split_id', 'track_id', 'answer_index', 'proof_path', 'pair_group')
hits=[]
for p in root.rglob('*.py'):
    text=p.read_text(encoding='utf-8')
    for token in forbidden:
        if token in text:
            hits.append((str(p), token))
assert not hits, hits
print('anti_leak_scan=PASS')
PY
```

Expected: `anti_leak_scan=PASS`.

- [ ] **Step 2: Run full v3 suite**

Run: `pytest tests/unified_v3 -q`
Expected: zero failures.

- [ ] **Step 3: Run relevant existing regression suite**

Run: `pytest tests/ftx1 tests/test_unified_v2* -q`
If the repository has no `tests/test_unified_v2*` match, run `pytest tests/ftx1 -q` plus the existing v2 test files discovered by `find tests -maxdepth 1 -iname '*unified*v2*' -o -iname '*preblind*'`.
Expected: zero failures in all discovered regression tests.

- [ ] **Step 4: Compile v3**

Run: `python -m compileall -q src/nexus_gllm/unified_v3`
Expected: exit 0.

- [ ] **Step 5: Write checkpoint report from actual fresh outputs**

The report must include exact commands, pass/fail counts, commit SHA, known P0 scope limits, and confirm that FTX1 BLIND content/gold/generator were not inspected.

- [ ] **Step 6: Commit report**

```bash
git add docs/results/2026-09-17-nexus-unified-v3-p0-report.md
git commit -m "docs(v3): record P0 verification checkpoint"
```

- [ ] **Step 7: Verify branch head and diff**

Run: `git status --short && git log -8 --oneline && git diff <P0_BASE_SHA>..HEAD --stat`
Expected: clean worktree; only approved v3/docs/test changes relative to the P0 base.

---

## Completion gate

Do not call P0 complete until Task 8 fresh verification evidence exists. In particular, architectural success is not implied merely by the existence of code. The report must demonstrate the two core properties from the design: semantic invariance across materially different surfaces and anonymous rule induction that survives operator/entity renaming while responding correctly to a real semantic intervention.
