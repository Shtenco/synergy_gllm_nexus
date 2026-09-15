# NEXUS CROSSGEN-1 Unified Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze a 12K post-freeze cross-generation benchmark, inventory every discoverable NEXUS release from GitHub/Drive/local artifacts, rerun every physically executable version without changing its reasoning logic, and publish a capability atlas including Russian, graph construction, far transfer and overfitting diagnostics.

**Architecture:** A deterministic benchmark generator produces six balanced sealed panels. A content-hash artifact inventory identifies unique NEXUS releases. Thin adapters translate common task records into each native runtime without adding reasoning. Results are stored per task and aggregated into capability metrics, evidence grades and paired statistics only where the same tasks were executed.

**Tech Stack:** Python 3.11+, stdlib, PyTorch/numpy/sklearn/catboost/joblib where required by historical releases, pytest, JSONL/ZIP/SHA-256.

**Spec:** `docs/superpowers/specs/2026-09-16-crossgen1-unified-nexus-benchmark-design.md`

## Global Constraints
- Benchmark design is frozen before reruns.
- CrossGen private task text is never used for training, model selection or adapter-specific lexical rules.
- Missing runtime = NR, never zero.
- Core CrossGen uses WEB=OFF for all generations.
- No modern LLM may replace a missing historical teacher.
- Historical-augmented and native-core modes are separate.
- Common-panel macro is only computed across task IDs both compared versions actually executed.

### Task 1: Deterministic sealed suite generator
**Files:** create `benchmarks/crossgen1/generate_crossgen1.py`, `benchmarks/crossgen1/schema.py`, `tests/test_crossgen1_generator.py`.
- [ ] Write RED tests for deterministic 12,000 count, six panels×2,000, stable task IDs, no duplicate normalized surfaces, balanced hop/language/OOD factors.
- [ ] Implement generator using seed 16092026 and private nonce namespaces.
- [ ] Write suite to `/mnt/data/crossgen1/frozen/CROSSGEN1_PRIVATE_12K.jsonl` without printing task text.
- [ ] Freeze SHA-256, generator SHA, counts and panel balance in `CROSSGEN1_FREEZE_MANIFEST.json`.

### Task 2: Artifact inventory and deduplication
**Files:** create `benchmarks/crossgen1/inventory.py`, `tests/test_crossgen1_inventory.py`.
- [ ] Scan `/mnt/data` NEXUS ZIP/checkpoint/report artifacts.
- [ ] Import 74-row historical audit metadata.
- [ ] Record GitHub/Drive source identifiers separately.
- [ ] Hash physical files and cluster byte-identical duplicates.
- [ ] Classify E3/E2/E1/E0 and write `crossgen1_artifact_inventory.json`.

### Task 3: Adapter contract and generic scoring
**Files:** create `benchmarks/crossgen1/adapters/base.py`, `benchmarks/crossgen1/scoring.py`, `tests/test_crossgen1_scoring.py`.
- [ ] Define `CrossGenTask`, `AdapterResult`, `NexusAdapter`.
- [ ] Implement exact/normalized answer scorers, coverage, abstention, graph triple scoring, FTI/XLT and OI component gaps.
- [ ] Implement paired bootstrap and McNemar from common task IDs.

### Task 4: Current Ω adapters
**Files:** create adapters for Ω-1.3/Ω-1.4/Ω-1.5/Ω-1.6-offline.
- [ ] Load frozen local checkpoints/results without retraining.
- [ ] Expose only panels their native interfaces support.
- [ ] Run smoke tasks before sealed execution using non-sealed fixtures.

### Task 5: Historical R7 adapters
**Targets:** R7.12, R7.14, R7.17, R7.18 and any other locally executable R7 freezes.
- [ ] Extract releases into isolated directories.
- [ ] Run native self-tests first and record outputs.
- [ ] Build thin adapters only when native runtime exposes a deterministic callable interface.
- [ ] Do not patch model logic; packaging/path shims are allowed and must be logged.

### Task 6: Earlier R6/R7.1–R7.4/Unified/V8/V10/V12/V30 candidates
- [ ] Inspect local and Drive physical releases.
- [ ] Classify as E3/E2/E1/E0.
- [ ] Execute native tests where possible.
- [ ] Add CrossGen adapter only if output semantics can be mapped without adding reasoning.

### Task 7: GitHub NEXUS candidates
**Targets:** `Shtenco/agi_nexus`, `Shtenco/nexus_science_agent`, `Shtenco/synergy_gllm_nexus`, and NEXUS-related generations discovered in connected repositories.
- [ ] Inventory generation directories/freeze records.
- [ ] Materialize only runtimes needed for current reruns.
- [ ] De-duplicate with Drive/local artifacts by hashes/version manifests.

### Task 8: Sealed execution
- [ ] Verify suite SHA before every adapter run.
- [ ] Execute each adapter in a fresh process with network disabled.
- [ ] Save raw per-task result JSONL + stdout/stderr + runtime metadata.
- [ ] Never modify suite after first execution.

### Task 9: Capability atlas and overfitting analysis
- [ ] Aggregate RU_LANG, GRAPH, REASON, CONTEXT, FAR_TRANSFER, OOD_OVERFIT.
- [ ] Compute FTI, XLT, G_surface/template/entity/domain/length and OI.
- [ ] Record coverage and NR separately.
- [ ] Compute paired statistics only for common task IDs.

### Task 10: Historical/native merge and report
- [ ] Merge CrossGen results with native historical evidence without converting native scores into CrossGen scores.
- [ ] Produce `docs/results/2026-09-16-crossgen1-capability-atlas.md` and machine-readable JSON/CSV.
- [ ] Explicitly identify which claimed historical improvements reproduce, fail to reproduce, or remain unverifiable.

### Task 11: Verification and repository integration
- [ ] Run CROSSGEN unit tests + protected Ω tests.
- [ ] Run `python -m compileall benchmarks src training`.
- [ ] Push generator, manifest, inventory, adapters, aggregate results and report to draft PR #1.
- [ ] Keep private task text out of GitHub; only generator/manifest/hashes and result aggregates are committed.
