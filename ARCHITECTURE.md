# NEXUS GLLM Ω-1 Architecture

## Principle

NEXUS GLLM Ω-1 treats a dynamic typed hypergraph as the primary cognitive state. Token sequences are only an I/O representation.

```text
text / events / memory
        │
        ▼
RussianGraphCompiler
        │
        ▼
DynamicHyperGraph ───────────────┐
        │                        │
        ▼                        │
WorkspaceRetriever              │ persistent memory
        │                        │
        ▼                        │
GraphRecurrentCore              │
        │                        │
        ├── neural op logits     │
        │                        │
        ▼                        │
policy-gated mutation / Rules ───┘
        │
        ▼
AnswerResolver
        │
        ▼
AnswerGraph
        │
        ├── DeterministicRussianRealizer (canonical fallback)
        └── NeuralGraphRealizer (experimental surface decoder)
```

## 1. Memory graph

`GraphCard` is the base memory unit. A card has identity, semantic type, label, optional latent state, confidence, activation, importance, prediction error, consolidation strength and provenance.

`TypedHyperEdge` can connect tuples of source and target nodes. Ordinary directed edges are simply one-source/one-target hyperedges.

`DynamicHyperGraph` owns:

- node store;
- edge store;
- active/inactive relation state;
- graph version;
- mutation log;
- deterministic JSON representation.

Long-term memory is not constrained to a language-model context window.

## 2. Working memory

`WorkspaceRetriever` selects a bounded active subgraph. Seeds are always retained, then graph neighbors and high-activation cards are added with deterministic tie-breaking.

The intended scaling model is:

```text
very large persistent graph
        ↓ retrieval / spreading activation
32–512 active cards
        ↓ recurrent graph cognition
new graph state / answer
```

## 3. Recurrent graph cognition

`GraphRecurrentCore` is implemented in plain PyTorch.

For each cognitive step it performs:

1. node projection into hidden state;
2. typed edge embedding;
3. message generation from source node + edge type;
4. destination aggregation;
5. global workspace pooling/broadcast;
6. gated recurrent node update via `GRUCell`;
7. learned activation gate;
8. operation classification.

Current operation head size is six and is reserved for:

`NOOP`, `ACTIVATE`, `SUPPRESS`, `LINK`, `RETRACT`, `ANSWER`.

The current runtime does **not** execute raw operation logits directly against persistent memory. Structural mutation remains policy-gated and deterministic until learned mutation passes dedicated tests.

## 4. Symbolic/neural hybrid

Ω-1 is intentionally hybrid.

The deterministic rule engine supplies exact graph transformations and training traces for capabilities that are easy to verify. Example:

```text
older_than(A,B)
older_than(B,C)
        ↓
older_than(A,C)
```

The recurrent neural core learns graph-state representations and operation decisions. Later generations can absorb more symbolic behavior only when they preserve correctness on frozen suites.

## 5. World revision

Some relations model mutable world state. In V1:

- `owned_by`
- `located_in`

are exclusive for the same source object. Adding a new active fact retracts the previous conflicting active edge while preserving it in history.

This separates:

- historical memory;
- current world state.

## 6. GraphScript

GraphScript is an inspectable interchange language rather than an internal Python execution mechanism.

```text
NODE anton : PERSON ["Антон"]
EDGE anton -> boris : older_than CONF=1.0
QUERY oldest(?)
ANSWER anton
```

It is used for fixtures, benchmark evidence, teacher traces and debugging.

## 7. Language

The first Russian compiler is deliberately deterministic and narrow. It establishes the contract that later learned parsers must beat without silently changing graph semantics.

Supported V1 relation families include:

- identity/class (`is_a`);
- age comparison (`older_than`);
- location (`located_in`);
- possession (`owned_by`).

## 8. Answer graph

Reasoning returns `AnswerGraph`, not prose. It records the answer value, intent, confidence, support nodes, support edges and provenance.

The text realizer is downstream of semantic answer selection.

This separation is crucial: language generation is not allowed to redefine the result of graph reasoning.

## 9. Neural Russian realizer

`NeuralGraphRealizer` is a small graph-conditioned GRU decoder. It is not a pretrained LLM and has no general knowledge of its own.

Its role is surface generation only. Until semantic-preservation gates are satisfied, `DeterministicRussianRealizer` remains the canonical output path.

## 10. Training

The current training pipeline produces synthetic transitive-reasoning graph tasks with disjoint entity identities across train/dev/blind splits.

`training.train_core` trains the recurrent core from scratch. No pretrained LLM weights are loaded.

Future losses may include node type, edge type, graph transition, structural operation, answer selection, confidence and graph-to-text losses, but only implemented losses may be reported.

## 11. Scaling hypothesis

The research hypothesis is that capability can scale through multiple independent axes:

- recurrent-core parameters;
- richer graph topology;
- larger persistent memory;
- better workspace retrieval;
- learned structural mutation;
- world-model/causal training;
- graph consolidation;
- richer language realization.

This is intentionally different from scaling only next-token Transformer parameter count.
