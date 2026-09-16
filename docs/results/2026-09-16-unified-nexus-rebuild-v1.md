# Unified NEXUS Rebuild v1 — frozen experimental build

## Status

`FROZEN_EXECUTABLE_EXPERIMENTAL` — the rebuild is no longer `BLOCKED / NR`. Three rebuilt checkpoint organs and an executable integration runtime were physically produced and hash-addressed. This does **not** claim unrestricted conversational Russian competence.

## Rebuilt checkpoint organs

- Ω-1.4R Semantic Operator — SHA-256 `aae4b5ddcb8b1d4375e1248d258b9f0a89fbb190621c497b9352b6bd2a9894da`
- Ω-1.5R Joint Argument — SHA-256 `f7f6d2447fffc2f6a97d36605b253a515bb8b38db0e2f7e37c197f6d4cb02487`
- Context/Revision Binder R — SHA-256 `85cbccb8ae0a70ec744bc8ca92b2bbf2e1be50c567f4e6b9e3aa858a26c8fef2`
- Unified runtime — SHA-256 `b5c0bae7dc433b8ea63d773a541f9c2272970a72a3f0f17e9633fd018866af83`

Protocol was frozen before weights. Pre-Blind checkpoint freeze was committed at `5f58cbd64a39861006fbdb27c4aa1a329b9a19b7`. Blind-A/B were opened once after that commit and were not used for post-hoc tuning.

## One-shot Blind results

| Suite | Relation | Candidate both recall | Strict triple with predicted relation |
|---|---:|---:|---:|
| Blind-A | 52.70% | 100.00% | 2.10% |
| Blind-B | 64.35% | 100.00% | 3.67% |

The measured bottleneck is role-conditioned argument binding, especially SUBJECT, rather than candidate recall.

## Frozen Integration-Bench v1

Integration benchmark manifest SHA-256: `e4630eb4335cf50dba818a6839d23fb9ca1e99c472ef8c0992f19afc29620d8a`.

| Capability | Result |
|---|---:|
| Structured far-transfer D1–D4 (`before`, `is_a`) | 640/640 = 100% |
| Context/revision queries | 1200/1200 = 100% |
| Evidence/trust joint decision | 400/400 = 100% |
| New RU E2E relation | 75.00% |
| New RU E2E SUBJECT exact | 33.17% |
| New RU E2E OBJECT exact | 58.33% |
| New RU E2E strict triple | 24.83% |

No scalar overall score is assigned. Averaging deterministic graph/state tests with language parsing would be misleading.

## Scientific boundary and next generation

This build validates an executable graph/context/evidence integration on frozen synthetic diagnostics. It does not establish unrestricted conversational fluency. The next generation should redesign SUBJECT/OBJECT role binding and must use a new pre-code blind suite rather than tune against the Blind-A/B disclosed by this build.
