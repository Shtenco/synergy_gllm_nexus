# NEXUS R1.3-X deep training report — 2026-09-26

## Scope

Recovery branch reviewed: `nexus-r13x-recovery-2026-09-26`.

The recovered R1.3-X is a recovery/upgrade line, not the byte-identical historical Unified R1.3. The historical manifest records the old 164/188 = 87.23% result and 30/30 open-set, but the original 188-case payload is not present in the recovered repository.

## Recovered architecture audit

The recovered runtime preserves:

- evidence-first Blackboard;
- authority ordering;
- exact verifier;
- contradiction abstention;
- open-set abstention;
- Unified V3 counterfactual/world/epistemic bridge.

The initial `R13XRouter` was deterministic and contained no trainable weights. Therefore a real trainable representation/router was added on a new derivative branch rather than modifying the recovery-original branch.

## Deep-training line

Branch: `nexus-r13x-deeptrain-2026-09-26`

Final learned representation:

- hashed subword representation;
- semantic concept features approximating the V4.2-style semantic layer;
- 9 capability classes: exact, formal, memory, causal, evidence, semantic, world, language, abstain;
- MLP capability router;
- immutable historical governor/verifier;
- high-precision authority gates ahead of learned routing.

### Phase 1

- train: 6,300
- dev: 1,080
- held-out blind: 1,080
- parameters: 34,857
- epochs: 18
- dev: 100%
- same-generator blind: 100%
- reconstructed category-matched compound-188: 188/188
- reconstructed open-set: 30/30

These scores were treated as insufficient evidence of generalization because the generator family overlapped.

### Surface-disjoint diagnostic

Fresh 45-case surface-disjoint set:

- 21/45 = 46.67%

This exposed template overfitting and was marked consumed.

### Phase 2

Broader paraphrase curriculum:

- train: 8,100
- dev: 1,350
- dev: 100%

Fresh HARD-2:

- 20/54 = 37.04%

Conclusion: adding paraphrases without changing representation did not solve far-surface transfer.

### Phase 3 — semantic concept encoder

Representation was upgraded to hashed subwords + explicit semantic concept features.

- train: 10,800
- dev: 1,620
- parameters: 54,985
- epochs: 18
- dev: 100%

Fresh HARD-3:

- 48/72 = 66.67%

Per-category:
- exact 4/8
- formal 5/8
- memory 5/8
- causal 6/8
- evidence 4/8
- semantic 5/8
- world 6/8
- language 7/8
- abstain 6/8

HARD-3 was then marked consumed.

### Phase 4 — hybrid authority routing

A high-precision semantic/authority gate was added ahead of learned routing.

Fresh HARD-4:

- 50/72 = 69.44%

HARD-4 was marked consumed.

### Final HARD-5

After fixing generic precedence failures (no-evidence abstention, exact dispatch, causal intervention, memory/world precedence), a completely new HARD-5 set was opened once.

**Final: 85/90 = 94.44%**

Per-category:

- exact: 10/10
- formal: 10/10
- memory: 10/10
- causal: 10/10
- evidence: 9/10
- semantic: 10/10
- world: 9/10
- language: 10/10
- abstain: 7/10

The historical governor/verifier regression remains 4/4.

## Historical benchmark comparison

Historical Unified R1.3 reference:

- 164/188 = 87.23%
- open-set 30/30

The original 188 cases are not recovered. Therefore the new R1.3-X result **must not be reported as a rerun of the historical 188-case benchmark**.

The category-matched reconstructed 188 score was 188/188, but it is same-taxonomy synthetic and is not comparable as a pristine historical rerun.

The strongest current fresh result is HARD-5 **85/90 = 94.44%**, which measures fresh surface/capability routing under the upgraded R1.3-X representation.

## Checkpoints

Local semantic-router checkpoint:

- file: `r13x_router_semantic_v3.pt`
- SHA-256: `c3a0509e7e482fda08b176481d2de43a98052897b3f65bb6ff70cb00b22acb55`

Initial learned-router checkpoint:

- file: `r13x_router_deep.pt`
- SHA-256: `baa38ef7fa5baa671f52c3dfb3f678591eaabe407df3c237562810041ad4bd2e`

Final HARD-5 report SHA-256:

- `8d29d8158824f2149a7decff25c6e7e436112f6416cfc937da29691ecd156e01`

## Infrastructure note

GitHub Actions for this private repository currently fails before the first job step and produces no artifacts. Therefore the completed training/evaluation was executed in the local runtime using the exact committed training logic; source code and immutable result hashes are recorded on this branch.

## Current scientific verdict

R1.3-X is now genuinely trainable. The important progression was:

`same-family 100% -> surface-disjoint 46.67% -> representation redesign -> 66.67% -> hybrid authority routing -> fresh HARD-5 94.44%`.

This supports a real improvement in capability routing and authority-preserving generalization for the new test family. It does not prove reproduction of the historical Unified R1.3 164/188 benchmark because that original case payload remains unavailable.
