# Unified R1.3 forensic recovery report — 2026-09-25

## Decision

**Recovery status: NOT RECOVERED.**

The exact original **Unified R1.3** release tree has not been recovered from the currently accessible Google Drive, GitHub organization, GitHub Actions artifacts/logs, ChatGPT Library, or recovered local archives.

The NEXUS-MOE-B2 artifact gate therefore remains **10/11** and **FAIL-CLOSED**.

NEXUS Unified RU v1, Unified NEXUS Rebuild v1, and later Unified v2 packages are successor/reconstruction lines. They are not accepted as the historical R1.3 artifact and must not be relabelled to satisfy the gate.

## What is proven about historical R1.3

Independent historical evidence establishes that the original R1.3 authority existed and was used by the R2 integration.

Preserved R2 freeze evidence:

- integration runner path: /mnt/data/run_nexus_r2_qwen_full_benchmark.py
- integration runner bytes: 23270
- integration runner SHA-256: 22f486b9872aeaeb46f8d84dc4e7ac8d6c61bfb727b12962d464756d598d3fc1
- sealed runner SHA-256: 83f4aa3bc045b6f545c710718390671249a135ec0a5d19ec8e96f23704e72ad9
- full R2 core + Unified regression: 37/37
- V4.2 legacy regression: 8/8
- V5.7 legacy regression: 7/7
- GitHub authority contract: 3/3
- development integration: 12/12, protected violations 0

Historical clean-extraction evidence records Unified R1.3 as the compound V4.2 + V5.7 + exact + logic + memory + executive system with exact 32/36, logic 20/20, causal 31/42, memory 12/12, aggregate 164/188 = 87.23%, open-set 30/30, and 117/117 frozen files unchanged.

These results establish historical existence and behavior, but they are not a substitute for the missing exact release bytes.

## Google Drive search

Historical lineage still visible:

- NEXUS V5 Graph Cognitive OS — 2026-08-01; folder 1biIbZrHjog59fSbua0yGIVeg1nxOU3zN
- NEXUS V5.7 Frozen-Core Sparse Synaptic MoE; folder 106q0wtcqxzP20ueHm6k9ciGwDUBSjH3F; created 2026-08-01 19:43Z
- NEXUS V5.8 Russian Cognitive Decoder; folder 1Hp-0huq7HdRIEcQgSKtfCV-g5JXwgsYI; created 2026-08-01 21:28Z
- NEXUS Unified R1 Foundation 0.1; folder 18clH7p12Yh9qlH4GhVF__D0sscFfd_Kq; created 2026-08-01 21:47Z

The V5.7, V5.8 and Unified R1 Foundation folders are currently empty. Targeted Trash queries by parent id returned no deleted children.

Exact Drive searches found no surviving copy of the frozen R2 integration runner, sealed runner, core/authority logs, or their known SHA-256 values. The preserved freeze paths point to temporary /mnt/data files.

## GitHub search

The Shtenco organization was rechecked across all 71 repositories. A corrected second pass explicitly searched branch names for r13, r1_3, r1-3, unified*r1, r1*unified, v5.7/v57 and v5.8/v58. No genuine R1.3/V5.7/V5.8 branch was found.

Organization-wide code search for the frozen runner/log names and exact SHA-256 values returned no match.

Comparing NEXUS V18 commit 252d6c221a202bbc57dc708d516c6dd8a00c8826 to preserved R2 baseline 23470f82d4b23336a8c10d232376ed34c0f90826 shows only R2-specific additions. No R1.3, V4.2 or V5.7 source tree entered Git in that transition.

The historical audit/all-nexus-intelligence-20260805 branch and PR #22 were also inspected; they add a V11–V20 reproducibility harness but contain no R1.3 tree or hidden R1.3 source manifest.

## GitHub Actions

The preserved R2 workflow run remains identifiable, but its retained artifacts are gone and the job-log blob now returns 404. Actions cannot reconstruct the deleted local runner or R1.3 tree.

## Recovered archive search

Available recovery packages were inspected for R1.3/V4.2/V5.7 names, internal paths, manifests and known hashes, including:

- NEXUS_ALL_VERSIONS_AUDIT_AND_EVIDENCE_2026-08-05.zip
- NEXUS_FULL_DRIVE_AUDIT_2026-09-15.zip
- NEXUS_R2.1_QWEN3_14B_SOURCE_ALPHA.zip
- NEXUS_R2.1_QWEN3_14B_SOURCE_PHASE2.zip
- NEXUS_UNIFIED_RU_V1_FULL.zip
- NEXUS_UNIFIED_REBUILD_V1_2026-09-16.zip
- NEXUS_UNIFIED_V2_RC1_FULL_REPRO_2026-09-17.zip
- NEXUS_LAST3_SOURCES_R7441_R7442_R7443_2026-08-30.zip
- R7.45.2 release package and relevant APK/source packages in the recovery workspace

None contains the exact original R1.3 release tree. The 2026-09-17 Unified v2 RC1 is a later reproduced release and does not satisfy the exact-artifact gate.

## Earlier OLGA donor line

Older Drive backups of agi_olga-main contain genuine modular organs such as cognitive_cycle.py, working_memory.py, memory_system.py, episodic_memory.py, semantic_memory.py, reasoning_engine.py and world_model.py. These are plausible architectural ancestors, but they predate the V4/V5/R1.3 lineage and cannot be promoted as byte-identical R1.3.

## Acceptance boundary

R1.3 may move from HISTORICAL_RELEASE_NOT_MOUNTED only if recovery yields either the original exact release tree/bundle, a byte-identical deployment/runtime cryptographically tied to R1.3 itself, or an immutable historical artifact containing the complete original tree with sufficient manifest/hash evidence.

Behavioral similarity, reconstructed organs, successor packages, historical scores and architecture descriptions are insufficient.

## Current NEXUS-MOE-B2 gate

Exact/recovered experts: R7-L, R7.2, R7.6, R7.8, R7.10, R7.14, R7.18, R7.44.3 exact deployed runtime, Omega-1.5R2, and V10 600K.

Blocked: Unified R1.3 — original exact release not recovered.

Therefore NEXUS-MOE-B2 / HARD-FAR-OOS readiness = 10/11; gate = FAIL-CLOSED; generation/opening = FORBIDDEN.

## Remaining recovery surface outside searched systems

The only credible remaining source is an external/offline copy not currently exposed to this workspace: an old workstation, local disk, download cache, browser/download folder, backup disk, another cloud location, or another archive not yet connected.

Until such bytes appear, the scientifically correct state is 10/11, not an inferred or reconstructed 11/11.
