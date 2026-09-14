# NEXUS GLLM Ω-1.1 — Neural Compiler, Temporal/Causal Graph and Sleep

**Date:** 2026-09-15  
**Status:** approved continuation of Ω-1 architecture  
**Repository:** `Shtenco/synergy_gllm_nexus`  
**Runtime constraint:** no pretrained LLM dependency

## 1. Goal

Extend Ω-1 with the three missing mechanisms required before large-scale Russian graph pretraining:

1. a **neural Russian → graph compiler** trained from scratch;
2. a **temporal/causal event graph** for changing world-state and event reasoning;
3. a deterministic **sleep/consolidation** pass that compresses episodic memory into stronger semantic structure.

The existing deterministic Russian compiler remains a verifier/fallback. The neural compiler is not permitted to write arbitrary persistent graph state directly.

## 2. Architectural choice

Ω-1.1 uses a structured neural parser rather than a seq2seq GraphScript generator.

### Recommended architecture

```text
Russian sentence
      ↓
CharVocab / character encoder
      ↓
BiGRU semantic encoder
      ↓
┌───────────────┬────────────────┬────────────────┬─────────────────┐
│ relation head │ subject pointer│ object pointer │ confidence head │
└───────────────┴────────────────┴────────────────┴─────────────────┘
      ↓
NeuralParseProposal
      ↓
ProposalValidator
      ↓
Graph mutation contract
      ↓
DynamicHyperGraph
```

This is deliberately not an LLM. The compiler predicts a small, explicit structured object. It is auditable, cheap to train and can later be replaced by a slot-based graph decoder without changing the mutation contract.

### Rejected A — text → GraphScript autoregressive decoder

This is easy to demo but recreates sequence generation failure modes, makes exact structural validation harder and spends parameters learning syntax rather than semantic graph construction.

### Deferred B — fully graph-generative slot decoder

A slot decoder that creates an arbitrary number of nodes/edges is the long-term Ω-2 direction. It is deferred until Ω-1.1 has stable benchmarks for relation/span extraction and graph mutation.

## 3. Neural compiler contract

```python
@dataclass(frozen=True)
class NeuralParseProposal:
    relation: str
    subject_text: str | None
    object_text: str | None
    subject_span: tuple[int, int] | None
    object_span: tuple[int, int] | None
    confidence: float
    kind: str  # statement | question | event | temporal | causal | abstain
```

Allowed initial relations:

- `is_a`
- `older_than`
- `located_in`
- `owned_by`
- `before`
- `after`
- `causes`
- `actor`
- `object`
- `abstain`

The compiler may abstain. Abstention is preferable to a low-confidence structural mutation.

## 4. Character-native encoder

Ω-1.1 uses a corpus-derived `CompilerCharVocab` and a bidirectional GRU:

- character embedding: 64;
- bidirectional hidden size: 128 per direction;
- pooled semantic vector: 256;
- token/span heads operate on character positions;
- relation head operates on pooled state;
- confidence is a sigmoid scalar calibrated on dev data.

The exact dimensions are configuration values in checkpoints and are not treated as architectural truth.

Character-level input avoids importing a tokenizer from an external LLM family and naturally covers Cyrillic morphology, punctuation and unseen names.

## 5. Structured validation

`ProposalValidator` enforces before mutation:

- relation is on the allow-list;
- spans are inside source text and non-empty;
- subject/object text exactly matches the proposed spans after normalization;
- confidence is above the relation-specific threshold;
- no self-loop for relations where it is invalid;
- exclusive relations (`owned_by`, `located_in`) use existing world-revision semantics;
- temporal and causal edges may not create an impossible cycle in strict mode.

Rejected proposals do not change persistent memory.

## 6. Temporal/causal event graph

### Event nodes

`NodeType.EVENT` represents a normalized event proposition. Event metadata contains:

- `status`: `observed | inferred | retracted`;
- `sequence_index`: optional integer;
- `time_label`: optional string;
- provenance;
- confidence.

### Relations

- `before(event_a, event_b)`
- `after(event_a, event_b)` normalized internally as reverse `before`;
- `causes(event_a, event_b)`
- `actor(event, entity)`
- `object(event, entity)`

### Required reasoning

- transitive temporal closure: `before(A,B) & before(B,C) -> before(A,C)`;
- causal ancestry: `causes(A,B) & causes(B,C) -> causal_path(A,C)`;
- cycle detection for `before` and strict causal DAG mode;
- retraction-aware traversal: inactive/retracted edges are ignored;
- safe query results include support edge IDs.

## 7. Deterministic event compiler bridge

Before the neural compiler is trusted, Ω-1.1 adds auditable Russian fixtures for:

- `Сначала <A>, потом <B>.` → two EVENT nodes + `before`;
- `<A>, поэтому <B>.` → two EVENT nodes + `causes`;
- `После <A> произошло <B>.` → `before(A,B)`;
- `Что было раньше: <A> или <B>?`
- `Что стало причиной <B>?`

These fixtures provide exact supervision for neural compiler training.

## 8. Sleep / consolidation

`GraphConsolidator` is a deterministic offline pass in Ω-1.1.

### Phase A — duplicate normalization

Nodes with identical `(type, normalized_label)` but different IDs are merged. Edges are rewired deterministically.

### Phase B — repeated evidence accumulation

Equivalent active edges are merged. Confidence is combined as:

```text
combined = 1 - Π(1 - confidence_i)
```

and capped to `[0,1]`.

### Phase C — contradiction cleanup

For exclusive relations (`owned_by`, `located_in`), only the latest/highest-supported active state remains active; weaker incompatible alternatives are retracted but retained historically.

### Phase D — consolidation strength

Cards and edges touched by repeated, non-contradictory evidence increase `consolidation_strength`.

### Phase E — semantic promotion

Repeated stable facts receive provenance `sleep:semantic` while original episodic evidence remains addressable through support metadata.

No memory is physically deleted in Ω-1.1. Forgetting/decay is deferred until there is a benchmark proving that it does not erase protected facts.

## 9. Training corpus

Extend synthetic generation with disjoint train/dev/blind entity and event surfaces.

Initial tasks:

- `relation_extract_older_than`
- `relation_extract_location`
- `relation_extract_ownership`
- `temporal_before`
- `causal_relation`
- `world_revision`
- `compiler_abstain`

Each record stores gold spans and relation:

```json
{
  "id": "train-causal-000001",
  "input_text": "Ливень усилился, поэтому дорогу затопило.",
  "compiler_target": {
    "kind": "causal",
    "relation": "causes",
    "subject_text": "Ливень усилился",
    "object_text": "дорогу затопило",
    "subject_span": [0, 14],
    "object_span": [24, 38]
  },
  "split": "train"
}
```

Blind surface templates must be disjoint from training templates, not merely use different names.

## 10. Neural compiler losses

```text
L =
  λ_relation * CE(relation)
+ λ_subject_start * CE(subject_start)
+ λ_subject_end * CE(subject_end)
+ λ_object_start * CE(object_start)
+ λ_object_end * CE(object_end)
+ λ_confidence * BCE(confidence)
```

Abstention examples train relation=`abstain` and do not contribute span loss.

Report every loss component separately.

## 11. Checkpoint contract

Compiler checkpoints contain only:

- `format_version`;
- explicit architecture config;
- char vocabulary;
- relation vocabulary;
- `state_dict`;
- seed;
- training manifest SHA;
- epoch/step metadata.

Runtime refuses incompatible relation vocabularies or dimensions.

## 12. Runtime integration

`NexusGLLM.learn()` becomes:

```text
text
 ↓
neural compiler (when checkpoint loaded)
 ↓
proposal validator
 ├─ accepted → graph mutation
 └─ rejected  → deterministic compiler fallback
 ↓
rules / temporal-causal closure
```

The response object records only safe structural traces and compiler confidence, never private chain-of-thought.

## 13. Benchmarks

### Compiler blind benchmark

At least 500 frozen cases:

- relation classification;
- exact subject span;
- exact object span;
- full-structure exact match;
- abstention precision/recall;
- mutation acceptance rate;
- invalid proposal rate.

Hard gates for promotion into default runtime:

- invalid accepted proposal rate: `0%`;
- strict structural exact match: `>=95%` on the frozen Ω-1.1 synthetic blind suite;
- abstention precision: `>=98%`;
- no blind-template overlap with train/dev by exact normalized template hash.

### Temporal/causal benchmark

At least 300 frozen cases:

- 1-hop before;
- multi-hop temporal closure;
- direct cause;
- multi-hop causal ancestry;
- cycle rejection;
- retraction-aware queries.

### Consolidation benchmark

At least 200 cases:

- duplicate merge;
- confidence accumulation;
- exclusive relation cleanup;
- persistence after sleep;
- protected fact retention.

## 14. Files

New focused modules:

```text
src/nexus_gllm/
  compiler_neural.py
  compiler_proposal.py
  temporal.py
  consolidation.py
training/
  generate_compiler_corpus.py
  train_compiler.py
benchmarks/
  run_compiler_benchmark.py
  run_temporal_benchmark.py
  run_consolidation_benchmark.py
tests/
  test_neural_compiler.py
  test_temporal.py
  test_consolidation.py
```

Existing `compiler_ru.py` remains the deterministic verifier/fallback.

## 15. Central invariant

> **The neural compiler may propose meaning; only validated graph operations may become memory.**

Ω-1.1 is successful when Russian text can be learned into graph structure by our own neural model, events can be reasoned over in time/causality, and memory can consolidate without relying on any pretrained LLM at inference.
