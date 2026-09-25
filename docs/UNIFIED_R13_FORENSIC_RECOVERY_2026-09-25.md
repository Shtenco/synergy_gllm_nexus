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

The Shtenco organization was rechecked across all 73 currently accessible repositories. A corrected pass explicitly searched branch names for r13, r1_3, r1-3, unified*r1, r1*unified, v4.2/v42, v5.7/v57, v5.8/v58, authority, cognitive and related NEXUS refs. No genuine historical R1.3/V5.7/V5.8 branch was found.

Organization-wide code and reachable-commit searches for R1.3, Unified R1, V5.7, V5.8, 164/188, 117/117, clean extraction, the frozen runner names, and exact runner/log SHA-256 values returned no original source artifact.

The complete early R2 commit chain was reconstructed. The branch starts from NEXUS V18 commit 252d6c221a202bbc57dc708d516c6dd8a00c8826 and then adds only R2/Qwen integration files: package interface, R2 system.py, benchmark runner, dependencies, CI, memory_v2, system_v2, tests, model manifest, authority-contract evidence, sealed set and final reports. No R1.3, V4.2 or V5.7 source tree was ever committed to the R2 Git branch.

PR #20 also describes the Git-side authority as exact arithmetic + NEXUS V18 formal implication + graph-memory facts. Therefore the later statement that R1.3/V4.2/V5.7 were physically connected refers to the separate local full-system runtime, not the public Git checkout.

The source-freeze ledger in Shtenco/synergy_agi_nexus was inspected. It requires a commit SHA plus artifact SHA-256 for promotion and freezes V18/V20/V21/R23/R7.4 sources, but contains no R1.3 promotion entry. This independently confirms that R1.3 lacked a retained reproducible source identity by 2026-08-21.

The historical audit/all-nexus-intelligence-20260805 branch and PR #22 were also inspected; they add a V11–V20 reproducibility harness but contain no R1.3 tree or hidden R1.3 source manifest.

## GitHub Actions

Actions history was paged back through the 2026-08-01/02 window.

A promising-looking branch, benchmark/81-unified-timing-v1, was recovered with multiple immutable head SHAs and workflow runs immediately before the Drive Unified R1 Foundation folder was created. Deep inspection proved it to be unrelated: it benchmarks 81 compression systems under compression_lab, with historical base c681ec94fe5194156b71fc304035f7aaff4d2327. It contains no cognitive Unified R1.3 code.

The R2 Actions sequence was also reconstructed from the earliest head SHAs through final 23470f82d4b23336a8c10d232376ed34c0f90826. Retained artifacts have expired and old job-log blobs return 404. The workflow's evidence manifest only hashes nexus_r2_qwen and scripts files; it does not package the external R1.3/V4.2/V5.7 local stack.

## R2 local freeze boundary

R2.0_BASELINE_AUDIT.json preserves the local frozen files and proves the external full-system execution:

- /mnt/data/run_nexus_r2_qwen_full_benchmark.py — 23270 bytes — SHA-256 22f486b9872aeaeb46f8d84dc4e7ac8d6c61bfb727b12962d464756d598d3fc1
- /mnt/data/run_nexus_r2_qwen_sealed_v1.py — 4494 bytes — SHA-256 83f4aa3bc045b6f545c710718390671249a135ec0a5d19ec8e96f23704e72ad9
- /mnt/data/NEXUS_R2_QWEN_SEALED_V1.json — SHA-256 f76a511984d190860cae3c9284f4a0ac248161744d4717a04df99a6a4352f378
- aggregate R2 freeze SHA-256 ebbfcfb18f1123bab8a3a6c81e80d411e4d7931200b447dc3a422e7a5ca20bd5

Important: the aggregate R2 freeze hash covers the listed R2 runner/model/runtime/report files. It is not a checksum of the historical 117-file R1.3 tree and cannot be used to promote R1.3.

The same baseline audit records full_r2_core_and_unified 37/37, v42_legacy 8/8 and v57_legacy 7/7, and notes that the compact V5.6 legacy test references a missing run_v56_cognitive_os.py entrypoint. Exact Drive/GitHub searches for that entrypoint returned no surviving copy.

## Recovered archive search

Available recovery packages were inspected recursively for R1.3/V4.2/V5.7 names, internal paths, manifests, known hashes, and candidate 117-file subtrees, including:

- NEXUS_ALL_VERSIONS_AUDIT_AND_EVIDENCE_2026-08-05.zip
- NEXUS_FULL_DRIVE_AUDIT_2026-09-15.zip
- NEXUS_R2.1_QWEN3_14B_SOURCE_ALPHA.zip
- NEXUS_R2.1_QWEN3_14B_SOURCE_PHASE2.zip
- NEXUS_UNIFIED_RU_V1_FULL.zip
- NEXUS_UNIFIED_REBUILD_V1_2026-09-16.zip
- NEXUS_UNIFIED_V2_RC1_FULL_REPRO_2026-09-17.zip
- NEXUS_LAST3_SOURCES_R7441_R7442_R7443_2026-08-30.zip
- R7.45.2 release package and relevant APK/source packages in the recovery workspace

No archive contains the exact original R1.3 release tree, and no candidate subtree with exactly 117 files was found.

NEXUS_UNIFIED_RU_V1_FULL is conclusively not hidden R1.3: its manifest names only R7.45.2, WorldGraph V12 and ARC V10 donor lines. Unified v2 RC1 points its v1 root to the later rebuilt Unified line, not historical R1.3. The 2026-09-16 rebuild is explicitly experimental/reconstructed and is not byte-identical evidence.

The 2026-08-05 all-version audit is the closest surviving historical ledger. It records Unified R1.3 as canonical compound cognitive OS (V4.2 + V5.7 + exact/logic/memory/executive), clean-extraction validation from 2026-08-02, 164/188, open-set 30/30 and 117/117 frozen files unchanged, but it contains no source path or per-file digest list for those 117 files.

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

The remaining credible source is an external/offline copy not exposed to the currently searched GitHub and Drive surfaces: an old workstation, local disk, browser/download cache, backup disk, another cloud account/location, or a previously generated archive that has not been reconnected.

Until such exact bytes or an immutable complete manifest appear, the scientifically correct state is 10/11, not an inferred or reconstructed 11/11.
