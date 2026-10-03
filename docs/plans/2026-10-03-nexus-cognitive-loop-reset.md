# NEXUS Cognitive-Loop Experimental Reset — 2026-10-03

## Purpose

Return NEXUS to the controlled cognitive-generalization program. No new NEXUS V8/V9/M33-style versioning is allowed by this plan until the gates below are closed with commit-bound evidence.

The central hypothesis to test is not "more modules = more intelligence". It is:

> State + Memory + Causal Model + Future Simulation + Verification + RPE + Recursive Credit Assignment + Meta-Control must produce measurable unseen-task gain over the same baseline at a fixed compute budget.

## 0. Canonical engineering baseline

Repository: `Shtenco/synergy_gllm_nexus`

Canonical CRC branch at reset start: `crc-r1-foundation`

Exact commit:

`cfa6de4d8b4c5e93444b2b9ff465557fdfe4bc9c`

Exact tree:

`a64c267fa68e1bacf06e8f4e2f7dd09af33a66dd`

This commit is an engineering baseline, not a claim of AGI/generalization success.

## 1. Historical cognitive lineage that must remain visible

| Lineage | Known evidence | Status for this reset |
|---|---|---|
| R7.17 | Blind-30 129/200 after recurrent + quantum-inspired routing | negative architectural evidence: added mechanisms alone did not improve the blind |
| R7.18 | Blind-31 156/200 = 78%; evidence/counterfactual credit | positive evidence for control/credit assignment |
| R7.18 multi-step | 28% vs 72% oracle | OPEN primary cognitive gap |
| R7.32 SUPRA | separate benchmark lineage known to exist | PROVENANCE UNRESOLVED until exact source/result ancestry is bound |
| R1.3-X / Unified V3 | executive/governor + cognitive runtime lineage | present in current repository; exact historical ancestry remains a separate provenance task |
| CRC-R1 | memory/causal/future/RPE/meta components | implementation exists; closed-loop cognitive gain NOT YET PROVEN |

Do not silently substitute a recovered/rebuilt package for an unresolved historical identity. Unknowns remain `UNRESOLVED`, not `PASS`.

## 2. Two experiment tracks are now explicitly separate

### Track A — M32.1 Neural Ingress

Question: can a pinned real neural model generate semantic/task/program proposals that the generalized ingress can safely admit and execute?

This is an ingress/proposal-quality experiment. It is NOT the AGI/CRC benchmark.

Current latest inspected DEV branch:

`m32-1-neural-dev-v7-pinned-schema-wire`

Head:

`f8c928ed68d45a07f279aab9de7488fde20856f9`

Pinned model:

`Qwen_Qwen3.5-0.8B-Q4_K_M.gguf`

SHA-256:

`fb044e93939a70469c905781334f5de1e6c8b608ced6cbc8c9249bd4127d9526`

Pinned llama.cpp source commit:

`4e7481175cbd4759df8bee2f1c1a0073effbebd7`

Latest real M32-DEV neural result observed on 2026-10-02:

- cases: 180
- unique real neural calls: 9
- ingress acceptance: 1.0
- provenance validity: 1.0
- task admission: 0.0
- program admission on solvable cases: 0.0
- E2E strict on solvable cases: 0.0
- unsafe authority promotions: 0
- unexpected adversarial admissions: 20

Verdict: `M32.1 DEV REAL NEURAL QUALITY = RED`.

`M32-META` must remain sealed while DEV is RED.

### Track B — CRC Cognitive Loop

Question: does the closed cognitive loop itself improve unseen cognitive performance beyond the baseline at the same compute budget?

This track must not inherit a GREEN verdict from M32/M32.1, CI, federation recovery, runtime identity, or authority tests.

## 3. Required gates — in order

### G0 — Canonical baseline / provenance

- bind this reset to the exact baseline commit above;
- recover/document exact R7.18 -> R7.32 -> Unified V3/R1.3-X ancestry where physically provable;
- unresolved historical identities stay unresolved.

### G1 — M32.1 DEV quality

Work on DEV only until neural proposal mapping is usable. Do not open M32-META. Any prompt/schema/compiler/runtime tuning is DEV evidence and must be frozen before META.

### G2 — Verified Proof DAG + Multi-Step State

Required behavior:

`task -> subtasks -> intermediate states -> proof nodes -> dependencies -> composed final proof`

A final answer is VERIFIED only when every required dependency node is covered by an allowed deterministic operation or verified proof.

The implementation must expose enough trace structure to assign credit to the actual failed intermediate step, not only to a final `program`/`answer` node.

Primary historical target: close the known `multi_step_algebra` gap without regressing other tracks.

### G3 — Cognitive Loop Ablation

Run the same frozen unseen benchmark and compute budget under:

- A: Memory
- B: Memory + Causal
- C: Memory + Causal + FutureTree
- D: Memory + Causal + FutureTree + RPE/Credit
- E: Memory + Causal + FutureTree + RPE/Credit + Meta

Minimum metrics:

- accuracy
- multi-step / long-chain accuracy
- causal intervention
- counterfactual
- long-horizon
- OOD
- calibration
- abstention
- memory retention
- forgetting
- negative transfer
- branch efficiency
- compute/token cost
- latency

Primary test:

`Gain = Performance(E) - Performance(A)` under fixed compute.

### G4 — Commit-bound PRE-FAR-OOS FREEZE

Freeze implementation commit, benchmark contract, seeds, budgets, scorer, dependency identities, prompts where relevant, and all hashes needed to reproduce execution.

### G5 — Fresh FAR-OOS

A newly generated untouched suite must include at least:

- multi-step
- causal intervention
- counterfactual
- long-horizon
- memory retention/forgetting
- cross-language
- unseen task-schema
- calibration/abstention

No tuning after first open.

### G6 — M32-META one-shot (conditional)

Open only if M32.1 is part of the frozen final CRC path and its DEV state has already been frozen.

### G7 — FTX2 creation

FTX1 is consumed. FTX2 must not be authored before the final implementation is frozen.

### G8 — FTX2 ONE-SHOT

Only one final verdict is allowed:

- `FAIL`
- `PARTIAL`
- `TRANSFER CONFIRMED`

The verdict must be tied to exact artifacts and must not be inferred from engineering CI.

## 4. Evidence-class rule

Every future report must distinguish:

- `ENGINEERING_GREEN`: code/tests/runtime/identity are valid;
- `DEV_COGNITIVE`: exposed development evidence;
- `FRESH_OOS`: first-open out-of-distribution evidence;
- `PRISTINE_BLIND`: untouched final evidence;
- `UNRESOLVED`: provenance or result not physically verified.

A lower evidence class may never be promoted to a higher class by wording.

## 5. Immediate implementation target

The current `CognitiveLoopR1` has real memory/meta/future/RPE/credit machinery, but its causal trace is too coarse for the historical multi-step gap. The next production change is therefore NOT a new top-level version. It is a tested extension of the existing CRC trace into a dependency-aware multi-step proof/state DAG.

TDD order:

1. RED: a two-step derivation must expose two intermediate dependency nodes and a final composed node.
2. GREEN: minimal DAG/state implementation.
3. RED: a failed intermediate node must receive local negative credit rather than blaming only the final answer.
4. GREEN: dependency-aware recursive credit propagation.
5. Regression suite.
6. Only then build the A/B/C/D/E benchmark harness.

## 6. Stop conditions

Do not:

- author FTX2 now;
- open M32-META while M32.1 DEV is RED;
- call CRC transfer confirmed from unit tests;
- create a new marketing/version label to bypass an open gate;
- treat CI success as unseen cognitive gain.

This document is the experiment contract for the reset branch.