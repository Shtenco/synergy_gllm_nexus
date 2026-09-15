# NEXUS GLLM Ω-1.2 — BeliefGraph, Contradiction Engine and Continual Learning

**Date:** 2026-09-15  
**Status:** approved architecture  
**Repository:** `Shtenco/synergy_gllm_nexus`  
**Runtime constraint:** no pretrained LLM dependency in canonical inference

## Goal

Extend Ω-1.1 with an auditable belief layer and continual-learning loop so NEXUS can ingest contradictory evidence, revise beliefs, learn source reliability, acquire new stable facts with zero gradient steps, and only update neural weights during gated sleep-training.

## Core invariant

> Neural components may propose propositions and updates. Evidence history, contradiction structure and final belief state remain explicit and auditable.

## Architecture

```text
Russian observation
      ↓
Neural Russian→Graph Compiler
      ↓
validated proposition
      ↓
Evidence Ledger
      ↓
BeliefGraph
  ↙         ↘
supports   attacks
  ↓           ↓
Contradiction Engine
      ↓
Belief Revision
      ↓
active / disputed / unknown / retracted
      ↓
Dynamic Semantic Graph
      ↓
Recurrent Graph Cortex
      ↓
AnswerGraph

Offline / Sleep:
new stable patterns
      ↓
Replay Buffer + protected memory
      ↓
small continual update
      ↓
legacy + new-task gates
      ↓
promote checkpoint or rollback
```

## Evidence model

Each evidence item stores:
- stable evidence id;
- proposition key;
- polarity: support / attack;
- source id;
- source reliability snapshot;
- confidence;
- timestamp/sequence index;
- provenance;
- optional support graph references.

No evidence is physically deleted in Ω-1.2.

## Source reliability

Each source maintains Beta-style reliability state:
- alpha >= 1;
- beta >= 1;
- posterior reliability = alpha / (alpha + beta);
- observed confirmations;
- observed contradictions;
- calibration metadata.

Source updates are deterministic and versioned.

## Belief state

A belief corresponds to a normalized proposition key `(relation, subject, object)`.

Stored fields:
- posterior probability;
- log-odds score;
- status: `active | disputed | unknown | retracted`;
- support evidence ids;
- attack evidence ids;
- contradiction set ids;
- provenance;
- last revision version.

Prior probability defaults to 0.5 unless an explicit authority prior is supplied.

## Revision rule

Each evidence contribution is converted to a signed log-likelihood-like increment:

```text
weight = logit(clamp(source_reliability * evidence_confidence, eps, 1-eps))
```

Support adds the weight; attack subtracts it.

Posterior is `sigmoid(total_log_odds)`.

Status thresholds:
- active: posterior >= 0.75 and contradiction mass below threshold;
- retracted: posterior <= 0.25;
- disputed: material support and attack are both present;
- unknown: otherwise.

Exact threshold values are constructor parameters and must be recorded in benchmark outputs.

## Contradiction engine

Contradiction sets are explicit graph objects.

Initial deterministic contradiction schemas:
- exclusive functional relations: same `(relation, subject)` with different objects for `owned_by`, `located_in`;
- direct negation / inverse polarity for identical proposition keys;
- temporal impossibility when strict `before` cycles would be introduced;
- mutually exclusive `is_a` classes only when an explicit exclusivity rule exists.

The engine does not invent ontology-level contradictions without a registered rule.

## Runtime API

```python
nexus.observe(
    text: str,
    source: str,
    confidence: float = 1.0,
    sequence_index: int | None = None,
) -> BeliefUpdate

nexus.belief(
    relation: str,
    subject: str,
    object: str | None = None,
) -> BeliefSnapshot | list[BeliefSnapshot]

nexus.correct_source(
    source: str,
    was_correct: bool,
    weight: float = 1.0,
) -> SourceReliability

nexus.sleep(
    continual_training: bool = False,
    ...
) -> ConsolidationReport | ContinualLearningReport
```

`observe()` first uses the Ω-1.1 compiler path. Accepted propositions become evidence records; evidence updates belief state; only sufficiently active beliefs are projected into the semantic world graph.

## Fast learning

New factual evidence changes graph memory and belief state immediately with zero gradient steps.

This is the default learning mode for ordinary facts.

## Slow continual learning

Neural weights are updated only during explicit sleep-training when enough new replay items have accumulated.

The continual trainer mixes:
- new-pattern batch;
- protected replay batch;
- optional hard-negative contradiction batch.

Promotion requires all gates:
- new-task metric improves by configured minimum;
- protected exact metrics do not regress beyond tolerance;
- protected semantic invariants remain 100%;
- invalid accepted mutation rate remains 0%;
- no benchmark contamination detected.

Otherwise the candidate checkpoint is rejected and previous checkpoint remains active.

## Replay buffer

Replay examples are immutable records with:
- task family;
- input/target structure;
- priority;
- protected flag;
- source generation;
- content hash.

Sampling policy in Ω-1.2 is deterministic weighted reservoir/replay with a protected quota.

## 100K corpus

Stage A target: exactly 100,000 train situations, plus separate dev and blind partitions.

Train composition:
- 20,000 ordinary relation learning;
- 15,000 contradictory evidence;
- 10,000 source reliability;
- 10,000 temporal revision;
- 10,000 causal evidence;
- 10,000 multi-source agreement;
- 10,000 continual-memory retention;
- 5,000 misinformation/correction;
- 5,000 abstention/unknown;
- 5,000 protected facts/rollback.

Dev target: 10,000. Blind target: 10,000.

Train/dev/blind must differ by entity namespaces, surface templates, source identities, evidence ordering patterns and contradiction compositions.

Every artifact receives SHA-256 manifests and template-hash summaries.

## Benchmark metrics

Belief benchmark:
- belief-state accuracy;
- posterior Brier score;
- contradiction detection precision/recall;
- source reliability calibration error;
- disputed/unknown classification accuracy;
- protected projection correctness.

Continual benchmark:
- new-task gain;
- legacy retention;
- catastrophic forgetting delta;
- protected exact retention;
- promotion/rollback correctness;
- knowledge acquisition cost measured as gradient steps for fact acquisition and pattern acquisition.

Target ordinary-fact acquisition cost: zero gradient steps.

## Scaling gates

Only after Stage A passes do we generate/train Stage B/C/D:
- 250K;
- 500K;
- 1M.

A failed gate stops scale-up.

## New modules

```text
src/nexus_gllm/
  evidence.py
  source_reliability.py
  belief.py
  contradiction.py
  continual.py
training/
  generate_belief_corpus.py
  replay_buffer.py
  train_continual.py
benchmarks/
  run_belief_benchmark.py
  run_continual_benchmark.py
  run_forgetting_benchmark.py
tests/
  test_belief_graph.py
  test_contradiction.py
  test_source_reliability.py
  test_continual_learning.py
```

## Non-goals

Ω-1.2 does not claim unrestricted factual truth or autonomous ontology construction. It does not erase evidence history, silently rewrite source reliability, or continuously fine-tune weights after every observation.
