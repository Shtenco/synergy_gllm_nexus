# Ω-1.6 prior-art audit — open research agents and search infrastructure

**Date:** 2026-09-16

This note records architectural donors for NEXUS Ω-1.6. It is not a ranking and does not import any external project as NEXUS authority.

| Project | Verified current repository state | Useful idea for NEXUS | Why not use as sovereign core |
|---|---|---|---|
| `assafelovic/gpt-researcher` | active public repository; README describes planner + execution agents, crawler workers, source tracking, >20-source reports, MCP and recursive deep research | planning/execution split, parallel retrieval, source tracking, MCP hybrid | final synthesis is still agent/LLM-centric; NEXUS needs claim/evidence authority below generation |
| `stanford-oval/storm` | active public repository; STORM + Co-STORM; README documents perspective-guided question asking, simulated expert conversation, dynamic mind map, many retrievers including SearXNG/Brave/Tavily/Google | graph-hole questions, multiple perspectives, iterative follow-ups, mind-map style evidence organization | designed for article curation/generation, not proof/evidence admission into a cognitive world graph |
| `LearningCircuit/local-deep-research` | active public repository; local/private research; README reports multi-engine agent strategy, encrypted local KB and security controls; project reports community SimpleQA/xbench results | dynamic engine routing, local/private mode, SearXNG, domain engines, security-first deployment, explicit benchmark diversity | benchmark scores depend on model/search configuration; LLM agent remains planner/authority unless restructured |
| `langchain-ai/open_deep_research` | public repository is archived | supervisor/researcher orchestration and configurable search/MCP patterns | archived dependency; architecture ideas are reusable, runtime dependency is undesirable |
| `bytedance/deer-flow` | active public repository | long-horizon orchestration, subagents, memory/sandbox patterns | broad super-agent runtime is much larger than the bounded evidence organ required by NEXUS |
| `firecrawl/web-agent` | active public repository | search/scrape/interact primitives and structured extraction | browser/search agent must remain a transport/extraction organ, not truth authority |
| `searxng/searxng` | active public metasearch repository | self-hosted federated search gateway | ranks results; does not validate truth/provenance itself |
| `jina-ai/reader` | active public repository | URL/search to normalized readable content | content normalization is useful but still untrusted external material |
| `browser-use/browser-use` | active public repository | dynamic/JS browser escalation | interactive browser must be sandboxed and read-only by default |

## Architectural synthesis

The strongest Ω-1.6 design is hybrid and sovereign:

- use external systems for **search, fetch, scrape and browser transport**;
- learn from research-agent orchestration for **question decomposition and gap discovery**;
- keep **ClaimProposal → EvidenceGraph → TrustGovernor → CitationLedger** native to NEXUS;
- never allow source rank, LLM synthesis, browser output or source-count majority to become truth automatically;
- keep `SEALED` and `OFFLINE` modes provably network-free.

## Benchmark lesson

Research systems should not be compared by a single headline score. A useful NEXUS research benchmark portfolio must separate:

1. factual retrieval correctness;
2. multi-hop browsing/research completion;
3. citation precision and coverage;
4. contradiction handling;
5. source independence/provenance;
6. EvidenceGraph correctness;
7. final answer/reasoning quality.

The Local Deep Research README, for example, reports strong SimpleQA and xbench-DeepSearch results under specific model/search configurations; those are valuable external reference points but not directly comparable to NEXUS graph-construction or historical R7.x Blind suites.