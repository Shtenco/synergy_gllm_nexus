# NEXUS GLLM Ω-1.6 Sovereign Research Cortex Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded, provenance-first internet research organ to NEXUS that runs a research probe for world-facing queries, escalates uncertain tasks to deep research, and admits web claims only through an EvidenceGraph/TrustGovernor pipeline.

**Architecture:** Ω-1.6 is an external knowledge organ layered above the frozen Ω-1.5 graph model. Search adapters return `SearchHit` proposals; normalization and extraction produce `ClaimProposal`s; the EvidenceGraph clusters provenance, support and contradiction; the TrustGovernor decides admission; the scheduler creates follow-up queries from unresolved graph holes. No retriever, browser agent, or external LLM receives truth or execution authority.

**Tech Stack:** Python 3.11+, stdlib networking interfaces, optional httpx/aiohttp adapters, pytest, existing NEXUS graph/Ω modules.

**Spec:** `docs/superpowers/specs/2026-09-16-omega16-sovereign-research-cortex-design.md`

## Global Constraints
- Frozen Ω-1.5 checkpoint and Blind-3 artifacts are read-only.
- `SEALED` and `OFFLINE` modes must make zero network calls.
- Web research has read-only capabilities and cannot execute external mutations.
- Every externally used answer claim must have provenance in `CitationLedger`.
- Search rank is not truth; duplicate/syndicated sources count as dependent evidence.
- SSRF protections must reject loopback, private, link-local, metadata endpoints and private redirects.
- Browser/Firecrawl are escalation adapters, never mandatory core dependencies.
- First-wave adapters: local retrieval, SearXNG, GitHub, arXiv, PubMed, Semantic Scholar.
- Tests use replay fixtures; live web access is never required for deterministic CI.

---

### Task 1: Research contracts and QueryGraph
**Files:**
- Create: `src/nexus_gllm/research/types.py`
- Create: `src/nexus_gllm/research/query_graph.py`
- Test: `tests/test_research_query_graph.py`

**Interfaces:**
- `ResearchMode = PROBE|DEEP|OFFLINE|SEALED`
- `SearchQuery`, `SearchHit`, `SourceRecord`, `ClaimProposal`, `ResearchNeed`, `VerifiedEvidence`
- `build_query_graph(text, graph_context, policy) -> QueryGraph`

- [ ] Write failing tests for freshness detection, explicit audit/deep-research intent, local-only arithmetic, user no-web flag and sealed benchmark context.
- [ ] Verify RED.
- [ ] Implement deterministic decomposition and mode selection.
- [ ] Require GREEN.

### Task 2: Safe transport and source normalization
**Files:**
- Create: `src/nexus_gllm/research/security.py`
- Create: `src/nexus_gllm/research/source_normalizer.py`
- Test: `tests/test_research_security.py`

**Interfaces:**
- `validate_public_http_url(url, resolver=None) -> ValidatedURL`
- `normalize_source(hit, content, redirects) -> SourceRecord`

- [ ] Test rejection of localhost, RFC1918, link-local, metadata IPs, file/ftp schemes and redirect-to-private.
- [ ] Test URL canonicalization, tracking-parameter stripping and content SHA-256.
- [ ] Implement minimal safe validation and normalization.
- [ ] Require GREEN.

### Task 3: Search federation
**Files:**
- Create: `src/nexus_gllm/research/search_federation.py`
- Create: `src/nexus_gllm/research/adapters/base.py`
- Create first-wave adapters under `src/nexus_gllm/research/adapters/`
- Test: `tests/test_search_federation.py`

**Interfaces:**
- `SearchAdapter.search(SearchQuery) -> list[SearchHit]`
- `SearchFederation.search(query, budget) -> list[SearchHit]`

- [ ] Write replay-fixture tests for deterministic merging, adapter failure isolation, engine quotas and canonical-ID deduplication.
- [ ] Implement local/SearXNG/GitHub/arXiv/PubMed/SemanticScholar adapters behind injectable transports.
- [ ] Enforce `SEALED/OFFLINE` network prohibition at federation boundary.
- [ ] Require GREEN.

### Task 4: Claim extraction and EvidenceGraph
**Files:**
- Create: `src/nexus_gllm/research/claim_extractor.py`
- Create: `src/nexus_gllm/research/evidence_graph.py`
- Test: `tests/test_evidence_graph.py`

**Interfaces:**
- `extract_claims(SourceRecord, omega14, omega15) -> list[ClaimProposal]`
- `EvidenceGraph.add_source/add_claim/add_support/add_contradiction`

- [ ] Write tests for atomic claims, exact support spans, same-origin clustering, contradiction edges and duplicate wire-copy grouping.
- [ ] Reuse Ω-1.4/Ω-1.5 graph extraction where compatible; use lower-trust text fallback otherwise.
- [ ] Require GREEN.

### Task 5: TrustGovernor and evidence mathematics
**Files:**
- Create: `src/nexus_gllm/research/trust_governor.py`
- Test: `tests/test_trust_governor.py`

**Interfaces:**
- `score_claim(claim_id, graph, query_context) -> ClaimDecision`
- statuses: `TRUSTED`, `CANDIDATE`, `CONFLICTED`, `REJECTED`.

- [ ] Test monotonicity for stronger direct/primary/fresh/independent evidence.
- [ ] Test that ten syndicated copies do not beat two independent primary sources.
- [ ] Test contradiction lowers confidence and may force `CONFLICTED`.
- [ ] Implement evidence weighting and dependency penalty from spec.
- [ ] Require GREEN.

### Task 6: ResearchScheduler and graph-hole loop
**Files:**
- Create: `src/nexus_gllm/research/scheduler.py`
- Test: `tests/test_research_scheduler.py`

**Interfaces:**
- `next_need(evidence_graph, budget) -> ResearchNeed | None`
- utility combines expected information gain, importance, novelty, cost, latency and risk.

- [ ] Test highest-utility selection, duplicate-query suppression, budget termination and no-novelty termination.
- [ ] Implement bounded iterative scheduling.
- [ ] Require GREEN.

### Task 7: CitationLedger and memory admission
**Files:**
- Create: `src/nexus_gllm/research/citation_ledger.py`
- Create: `src/nexus_gllm/research/memory_admission.py`
- Test: `tests/test_citation_ledger.py`

- [ ] Test that externally supported claims cannot render without source/support-span IDs.
- [ ] Test session/cache/promoted tiers and freshness expiry.
- [ ] Implement content-addressed cache metadata and revalidation policy.
- [ ] Require GREEN.

### Task 8: ResearchReflex orchestration
**Files:**
- Create: `src/nexus_gllm/research/reflex.py`
- Test: `tests/test_research_reflex.py`

**Interfaces:**
- `ResearchReflex.run(query, graph_context, policy) -> ResearchResult`

- [ ] Test PROBE, escalation to DEEP, OFFLINE, SEALED, contradictory evidence and partial-adapter failure.
- [ ] Require every world-query to execute at least a bounded probe unless explicit policy exempts it.
- [ ] Keep graph admission separate from retrieval.
- [ ] Require GREEN.

### Task 9: Historical benchmark/audit ledger
**Files:**
- Create: `docs/results/2026-09-16-nexus-cross-generation-audit.md`
- Create: `benchmarks/nexus_history_ledger.json`

- [ ] Import the 74-version Drive audit and independently surfaced R7.x/V8 artifacts.
- [ ] Add Ω-1.2/1.3/1.4/1.5 verified results with checkpoint/result hashes where available.
- [ ] Record native protocol, evidence grade, artifact availability, capability class and comparability notes.
- [ ] Never numerically rank scores from different Blind protocols as if they were the same task.
- [ ] Produce capability-wise comparisons: language/binding, exact triples, reasoning/governor, context, research/web, domain specialist, procedural/ARC.

### Task 10: Research benchmark harness
**Files:**
- Create: `benchmarks/run_research_benchmark.py`
- Create: `tests/test_research_benchmark.py`

- [ ] Implement replayable factual/citation/evidence-graph metrics using fixtures.
- [ ] Add adapters for external benchmark import formats: SimpleQA-like, BrowseComp-like and report/citation evaluation.
- [ ] Keep each benchmark score separate; no synthetic composite leaderboard by default.
- [ ] Require GREEN.

### Task 11: Integration, verification and PR
- [ ] Run targeted Ω-1.6 tests plus protected Ω-1.5 tests.
- [ ] Run `compileall`.
- [ ] Verify sealed benchmark mode makes zero adapter network calls.
- [ ] Verify no Ω-1.5 checkpoint/hash changes.
- [ ] Push verified sources and cross-generation audit to `nexus-gllm-omega1-v1`.
- [ ] Update draft PR #1 with Ω-1.6 research-core status and benchmark caveats.
