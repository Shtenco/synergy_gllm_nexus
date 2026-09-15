# NEXUS GLLM Ω-1.3 — Graph Construction Cortex

**Date:** 2026-09-15  
**Status:** approved direction, awaiting written-spec review  
**Repository:** `Shtenco/synergy_gllm_nexus`  
**Runtime constraint:** no pretrained LLM dependency in canonical runtime or Ω-1.3 training

## 1. Goal

Replace the narrow Ω-1.2 `relation + four span heads` compiler with a stronger, still auditable, **Graph Construction Cortex** that learns `Russian text -> graph construction` directly from the frozen Stage A corpus.

Ω-1.3 must be trainable locally on CPU in the current environment:

- PyTorch 2.10 CPU;
- 5 logical CPUs available to the worker;
- ~5.8 GiB RAM total;
- no CUDA.

The first Ω-1.3 model therefore targets approximately **2–8 million trainable parameters**, not a large Transformer-scale model.

## 2. Frozen evaluation contract

The existing Stage A compiler corpus is the canonical basis:

- train: 100,000 examples;
- dev: 10,000 examples;
- blind: 10,000 examples;
- raw corpus SHA-256: `738a8457f38ec8eb75ccc85bd18f713d5df8611e267900f8747de7f78ceebf2a`;
- blind is not used for architecture choice, threshold tuning, early stopping, vocabulary fitting or checkpoint selection.

Observed corpus properties:

- relations: `owned_by`, `located_in`, `is_a`, `older_than`, `before`, `causes`, `abstain`;
- max input length: 83 characters;
- mean input length: ~46.7 characters;
- character alphabet in the frozen corpus: 61 characters;
- `owned_by` is intentionally class-imbalanced and dominates the relation distribution.

Ω-1.2 frozen baseline:

- dev relation accuracy: 40.0%;
- blind relation accuracy: 40.0%;
- dev strict graph structure accuracy: 0.0%;
- blind strict graph structure accuracy: 0.0%.

## 3. Architectural choice

Ω-1.3 uses a **slot-based graph construction model** rather than a larger single-relation classifier.

```text
Russian characters
      ↓
Character + local morphology features
      ↓
Bidirectional recurrent semantic encoder
      ↓
Context states H[1..L]
      ↓
Learned graph slots
  ┌─────────────┬─────────────┬─────────────┐
  │ subject slot│ object slot │ relation slot│
  └─────────────┴─────────────┴─────────────┘
      ↓
Cross-attention-like pointer scoring over H
      ↓
Iterative graph-slot refinement (K steps)
      ↓
GraphConstructionProposal
      ↓
ProposalValidator
      ↓
DynamicHyperGraph
```

This remains **not an LLM**. It does not autoregressively generate GraphScript or prose.

## 4. Why this architecture

Ω-1.2 failed strict structure because relation classification and independent span heads do not model the dependency between:

- what the subject is;
- what the object is;
- which relation connects them;
- whether the sentence should abstain.

Ω-1.3 therefore makes these predictions from interacting latent graph slots rather than six mostly independent heads.

### Rejected A — just increase BiGRU hidden size

This changes capacity but not the structural bottleneck that produced 0% strict graph accuracy.

### Rejected B — autoregressive GraphScript decoder

This spends compute learning serialization syntax, introduces sequence decoding errors and moves the design back toward ordinary language-model behavior.

### Deferred C — arbitrary unbounded graph generation

The Stage A corpus currently contains at most one proposition per compiler record. Ω-1.3 reserves multiple slots but trains one active proposition slot plus `NO_NODE`/`NO_EDGE` states. Multi-proposition sentences are an Ω-1.4 corpus expansion, not silently invented in Ω-1.3.

## 5. Input representation

### 5.1 Character vocabulary

The vocabulary is fit on **train only**.

Special symbols:

- `<PAD>`
- `<UNK>`

No external tokenizer is used.

### 5.2 Local morphology features

Each character position receives learned or deterministic local features in addition to the character embedding:

- Unicode category bucket;
- is-letter;
- is-digit;
- is-uppercase;
- punctuation/space marker;
- local word-boundary marker;
- relative position bucket.

These features do not use external morphology libraries or pretrained embeddings.

## 6. Semantic encoder

V1 local CPU configuration:

- char embedding: 48;
- morphology projection: 16;
- 2-layer bidirectional GRU;
- hidden size: 96 per direction;
- encoder output: 192;
- dropout: 0.10 between recurrent layers.

These values are hyperparameters, not permanent architecture constants.

## 7. Graph slots

The model contains learned latent slots:

- `SUBJECT`;
- `OBJECT`;
- `RELATION`;
- optional `EVENT_A`;
- optional `EVENT_B`;
- `GLOBAL`.

For Stage A, event slots share the same pointer machinery and are used by `before`/`causes` supervision.

Each slot has dimension 192.

## 8. Iterative refinement

For `K=3` refinement steps:

1. each slot scores all encoder positions;
2. masked softmax produces a context summary;
3. slot receives the global summary and the other slots' current states;
4. a GRUCell updates the slot;
5. relation slot broadcasts a relation-conditioned bias back to subject/object slots.

This gives a small recurrent graph-building process without Transformer self-attention over long token sequences.

## 9. Output contract

```python
@dataclass(frozen=True)
class GraphConstructionProposal:
    relation: str
    subject_span: tuple[int, int] | None
    object_span: tuple[int, int] | None
    subject_text: str | None
    object_text: str | None
    confidence: float
    abstain: bool
    node_slots: tuple[GraphNodeProposal, ...]
    edge_slots: tuple[GraphEdgeProposal, ...]
```

For Stage A:

- one subject node slot;
- one object node slot;
- one relation edge slot;
- unused slots are explicitly `NO_NODE` / `NO_EDGE`.

Runtime conversion to `NeuralParseProposal` remains available for compatibility with Ω-1.2 `ProposalValidator` and `NexusGLLM.learn()`.

## 10. Span construction

Subject and object spans are predicted jointly by slot-conditioned start/end pointer heads.

For each slot:

```text
start_logits[i] = f_start(H_i, slot)
end_logits[i]   = f_end(H_i, slot)
```

Decoding searches valid `(start,end)` pairs with:

- `0 <= start < end <= text_length`;
- configurable maximum span width;
- score = start_score + end_score;
- no reliance on greedy independent argmax when a higher-scoring valid pair exists.

## 11. Relation construction

The relation classifier uses:

- refined relation slot;
- subject span summary;
- object span summary;
- global semantic summary.

Initial relation vocabulary is frozen to the 7 Stage A classes.

Class-balanced cross entropy is used because `owned_by` is overrepresented.

## 12. Confidence and abstention

Confidence is a calibrated scalar predicted from the final global/relation state.

`abstain` is both:

- an explicit relation class;
- a runtime gate when structure confidence is below threshold.

Threshold tuning uses dev only.

## 13. Training losses

```text
L =
  λ_rel * balanced_relation_CE
+ λ_sub_start * subject_start_CE
+ λ_sub_end * subject_end_CE
+ λ_obj_start * object_start_CE
+ λ_obj_end * object_end_CE
+ λ_span_valid * invalid_span_penalty
+ λ_conf * confidence_BCE
+ λ_consistency * graph_slot_consistency
```

`abstain` rows contribute relation/confidence loss but do not contribute subject/object span loss.

Every component must be logged separately.

## 14. Curriculum

Local training uses three phases on **train/dev only**:

### Phase 1 — span warm-up

Train subject/object pointers plus encoder while relation loss remains enabled at reduced weight.

### Phase 2 — joint graph construction

Train full objective.

### Phase 3 — hard-example refinement

Oversample dev-like difficult train examples based on training loss only. Dev is used for checkpoint selection, never resampled into train.

No blind access occurs before the selected checkpoint is frozen.

## 15. Local training budget

Because the environment is CPU-only, Ω-1.3 V1 uses:

- batch size: 128 when memory permits, otherwise deterministic fallback to 64;
- max sequence length: 96;
- AdamW;
- mixed precision disabled on CPU;
- gradient clipping: 1.0;
- deterministic seed: 17;
- early stopping on dev strict graph accuracy with patience 2;
- maximum 8 epochs for the first local run.

A smaller diagnostic model is permitted first to validate the training path, but the final reported checkpoint must come from the full 100K train partition.

## 16. Evaluation

### Dev metrics

Used for model selection:

- relation accuracy;
- macro relation F1;
- subject exact span;
- object exact span;
- both-spans exact;
- strict graph structure accuracy;
- abstention precision/recall/F1;
- confidence Brier score.

### Blind metrics

Blind is opened exactly once for the selected checkpoint.

Primary promotion metric:

- strict graph structure accuracy.

Secondary metrics:

- relation accuracy;
- macro F1;
- span exact metrics;
- abstention F1;
- invalid accepted proposal rate.

## 17. Promotion gate to 250K

Ω-1.3 permits Stage B 250K generation only if the frozen blind run shows:

1. strict graph structure accuracy **strictly greater than the Ω-1.2 0% baseline**;
2. blind relation accuracy **strictly greater than 40% baseline**;
3. invalid accepted proposal rate = 0% after validator;
4. no train/dev/blind content-hash contamination;
5. no blind use during checkpoint selection.

A stronger research target is >=80% strict graph accuracy, but failure to hit 80% does not erase measured progress; it only blocks claims of mature parsing.

## 18. Files

```text
src/nexus_gllm/
  graph_cortex.py
  graph_cortex_schema.py
training/
  train_graph_cortex.py
  graph_cortex_dataset.py
benchmarks/
  run_graph_cortex_benchmark.py
tests/
  test_graph_cortex.py
  test_graph_cortex_dataset.py
```

Ω-1.2 compiler remains intact as baseline/fallback.

## 19. Checkpoint contract

Checkpoint contains:

- format version;
- architecture config;
- train-only character vocabulary;
- relation vocabulary;
- model `state_dict`;
- seed;
- train corpus SHA;
- selected epoch;
- dev metrics at selection;
- loss weights;
- decoder thresholds.

No blind metrics are stored in the training checkpoint because blind is evaluated after checkpoint selection.

## 20. Scientific boundary

Ω-1.3 is an experiment in graph-native structured language understanding on a synthetic Russian Stage A corpus. It does not claim unrestricted Russian understanding or SOTA performance. A successful blind result justifies expanding corpus diversity and scale; it does not by itself validate the architecture on natural open-domain Russian.
