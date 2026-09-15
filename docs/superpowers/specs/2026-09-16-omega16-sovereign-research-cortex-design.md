# NEXUS GLLM Ω-1.6 — Sovereign Research Cortex

**Date:** 2026-09-16  
**Status:** approved by user  
**Runtime invariant:** external web/search systems provide evidence proposals only; they never become NEXUS truth or execution authority.

## 1. Goal
Ω-1.6 adds a graph-native internet research organ to NEXUS. Every world-facing user query triggers a bounded `ResearchReflex`; difficult/fresh/uncertain queries may escalate to multi-step deep research. Web content is converted into provenance-tracked evidence and admitted to the NEXUS world graph only through verification/trust policy.

Ω-1.5 remains frozen. Ω-1.6 does not retrain or modify its checkpoint.

## 2. Historical NEXUS compatibility
Reuse established NEXUS invariants:
- inference/read/telemetry is separated from execution authority;
- learned/retrieved evidence is not trusted merely because it was retrieved;
- authority, provenance and verification are explicit;
- R7.x BM25/Fuzzy/SEARCH_RRF remains a local retrieval organ, not internet authority;
- external tools are bounded organs behind capability contracts.

## 3. External prior art used as architectural guidance
Borrow primitives/ideas, not sovereign reasoning:
- GPT Researcher: query planning, parallel research, citation-oriented reports;
- STORM/Co-STORM: perspective questions and iterative gap discovery;
- Local Deep Research: dynamic search-engine federation and local/private search;
- Open Deep Research: configurable supervisor/researcher and MCP/search adapters;
- DeerFlow: long-horizon subagent orchestration patterns;
- Firecrawl Web Agent: search/scrape/browser primitives and structured extraction;
- SearXNG: self-hosted metasearch HTTP API;
- Jina Reader/Search: URL/search -> normalized readable text;
- Browser Use: interactive browser fallback for JS/dynamic sites.

None of those frameworks is the NEXUS authority or canonical runtime backbone.

## 4. Architecture

```text
USER QUERY
  -> QueryGraph
  -> ResearchReflex
     -> SearchFederation
        -> local BM25/Fuzzy/RRF
        -> SearXNG
        -> GitHub
        -> arXiv
        -> PubMed
        -> Semantic Scholar
        -> optional Jina / Tavily / Exa / Brave
        -> Firecrawl / BrowserUse escalation
  -> SourceNormalizer
  -> ClaimExtractor
  -> EvidenceGraph
  -> TrustGovernor
  -> ResearchScheduler / graph-hole loop
  -> VerifiedEvidenceSet
  -> NEXUS world graph
  -> Ω-1.4 / Ω-1.5 reasoning
  -> AnswerGraph + CitationLedger
```

## 5. QueryGraph
`QueryGraph` decomposes a request into explicit research needs without requiring an external LLM:
- original query;
- normalized semantic query;
- time/freshness requirement;
- domain hints;
- claims/questions to resolve;
- known graph facts;
- unresolved graph holes;
- research budget and privacy/capability policy.

Initial decomposition uses deterministic rules + NEXUS graph state. Optional external model planners may propose additional subquestions, but their proposals enter quarantine like any other evidence.

## 6. ResearchReflex
Every world-facing request receives at least a bounded probe unless policy marks it `NO_WEB_NEEDED` (pure arithmetic, local-only transformation, user explicitly disables web, or a sealed benchmark path).

Modes:
- `PROBE`: 1–2 reformulations, small top-k, low latency/cost;
- `DEEP`: graph-hole-driven subqueries, parallel engines, iterative corroboration;
- `OFFLINE`: local retrieval only;
- `SEALED`: no network access for frozen benchmark/training workflows.

Escalate from PROBE to DEEP on high freshness, high uncertainty, contradictory evidence, multi-hop graph holes, or explicit research/audit intent.

## 7. Search federation contract
Each adapter implements:

```python
SearchAdapter.search(query: SearchQuery) -> list[SearchHit]
```

`SearchHit` contains engine, canonical URL/identifier, title, snippet, published/retrieved timestamps when available, source type, rank, raw relevance, and provenance metadata.

Adapters never mutate the NEXUS graph directly.

Required first-wave adapters:
- local retrieval;
- SearXNG;
- GitHub;
- arXiv;
- PubMed;
- Semantic Scholar.

Optional/escalation adapters:
- Jina Reader/Search;
- Tavily/Exa/Brave;
- Firecrawl;
- Browser Use.

## 8. Source normalization and security
`SourceNormalizer` canonicalizes URL/DOI/repository identifiers, strips tracking fragments, hashes content, records redirects, content type, byte length and timestamps.

Network transport must reject:
- localhost / loopback;
- RFC1918/private IPs;
- link-local ranges;
- cloud metadata endpoints;
- non-http(s) schemes;
- redirects into blocked address ranges;
- oversized responses;
- disallowed content types.

DNS/IP policy is rechecked on every redirect hop. Browser escalation runs in a sandbox with read-only web capability.

## 9. Claim extraction
Fetched documents are not inserted wholesale into trusted memory. `ClaimExtractor` emits atomic `ClaimProposal` records:

```text
claim_id
canonical_subject
canonical_relation
canonical_object/value
claim_text
support_span
source_id
retrieved_at
published_at
extractor_confidence
```

Ω-1.4 semantic operators and Ω-1.5 argument construction are preferred for graph-compatible extraction; text-only fallback claims remain lower-trust evidence.

## 10. EvidenceGraph
Nodes:
- `SourceNode`;
- `DocumentNode`;
- `ClaimNode`;
- `ResearchNeedNode`;
- existing NEXUS graph entities/events.

Edges include:
- `supports`;
- `contradicts`;
- `derived_from`;
- `quotes`;
- `same_origin_cluster`;
- `updates`;
- `answers_need`.

Duplicate/syndicated sources are clustered so ten copies of one wire story do not count as ten independent sources.

## 11. Evidence scoring
For source i and claim c:

`w_i(c) = R_i * F_i * D_i * Q_i * C_i * I_i`

where:
- `R`: historical/source reliability;
- `F`: freshness relative to query;
- `D`: directness/primary-source factor;
- `Q`: retrieval semantic relevance;
- `C`: claim-span support consistency;
- `I`: independence factor.

Aggregate log evidence:

`L(c) = L0(c) + sum_i sign_i*w_i - lambda*sum_{i<j} dependency(i,j)*min(w_i,w_j)`

`sign_i` is +1 for support and -1 for contradiction. The score is advisory evidence; policy thresholds decide `TRUSTED`, `CANDIDATE`, `CONFLICTED`, or `REJECTED`.

## 12. TrustGovernor
Trust policy prioritizes:
1. direct primary authoritative source;
2. multiple independent high-quality corroborations;
3. reliable secondary source;
4. weak/unknown secondary material;
5. anonymous/duplicated/SEO content.

A single source may be sufficient only for facts for which that source is the direct authority (e.g. repository release metadata from the repository itself). Contested or analytical claims require corroboration.

Internet evidence cannot override protected NEXUS invariants or sealed benchmark state.

## 13. ResearchScheduler
Unresolved graph uncertainty creates `ResearchNeed` objects. Candidate next queries receive utility:

`U(q) = E[DeltaH(Graph)|q] * Importance(q) * Novelty(q) / (Cost(q)+Latency(q)+Risk(q))`

The scheduler chooses the highest-utility query and stops when:
- all required claims satisfy evidence thresholds;
- no query has utility above epsilon;
- the budget is exhausted;
- repeated queries yield no novel evidence.

## 14. CitationLedger
Every answer claim that depends on external evidence records the exact supporting source IDs and support spans. Citation rendering is downstream of the ledger; NEXUS never fabricates a citation that is absent from the evidence graph.

## 15. Memory admission
Web evidence has three tiers:
- session evidence: temporary;
- cached evidence: content-addressed, revalidatable;
- promoted world knowledge: admitted only after trust/provenance checks.

Promotion stores source hash, retrieval time, evidence score and invalidation/expiry policy. Freshness-sensitive facts must be rechecked before reuse.

## 16. Capability boundaries
Ω-1.6 may have `READ_WEB` and local cache-write capability.
It does not receive implicit permissions for:
- external account login;
- payments/trades;
- sending messages;
- file uploads to third parties;
- executing downloaded code;
- browser actions that mutate external state.

Such actions require separate explicit grants outside Ω-1.6.

## 17. Testing and benchmarks
Internal unit/property tests:
- URL canonicalization and SSRF guards;
- duplicate/source-independence clustering;
- evidence score monotonicity;
- contradiction handling;
- citation provenance completeness;
- scheduler termination;
- sealed/offline network prohibition;
- adapter deterministic replay using fixtures.

Research benchmarks are reported separately rather than collapsed into one score:
- SimpleQA-like factual retrieval accuracy;
- BrowseComp-like multi-hop browsing success;
- DeepResearch Bench-style report/citation quality;
- citation precision/coverage;
- source independence and contradiction calibration;
- NEXUS-specific `EvidenceGraph correctness` on a frozen synthetic+real source suite.

## 18. Historical comparison protocol
Previous NEXUS versions are compared on two axes:
1. `native evidence`: their own frozen/sealed benchmark and limitations;
2. `cross-generation capability`: whether the artifact actually implements the capability being compared.

Scores from different historical Blind suites are never treated as a common leaderboard. Missing physical artifacts or referenced-only weights are marked explicitly.

## 19. Scientific boundary
Ω-1.6 is an external evidence acquisition/verification organ, not proof of AGI or unrestricted truth discovery. Search-engine rank and web consensus are not truth. Benchmarks must report source/model/tool configuration and distinguish retrieved factuality, research completeness, citation correctness and final reasoning quality.