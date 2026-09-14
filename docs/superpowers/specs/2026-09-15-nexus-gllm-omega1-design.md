# NEXUS GLLM Ω-1 — Graph Latent Language Model

**Date:** 2026-09-15  
**Status:** approved architecture  
**Runtime constraint:** no pretrained LLM dependency  
**Repository:** `Shtenco/synergy_gllm_nexus`

## 1. Goal

Build a new graph-native language model in which the primary computational state is a **dynamic typed hypergraph**, not a token sequence processed by a Transformer LLM.

NEXUS GLLM Ω-1 must support the end-to-end path:

```text
Russian text / memory / world state
        -> Graph Compiler
        -> Dynamic Hypergraph
        -> Recurrent Graph Cognition
        -> Answer Graph
        -> Graph-to-Russian Realizer
        -> Russian text
```

The first release is a falsifiable research system. It must make no AGI/SOTA claims without named, frozen, reproducible benchmarks.

## 2. Central invariant

**Graph state is the cognitive substrate. Text is an interface.**

No Qwen, Llama, Mistral, GPT, or other pretrained LLM is allowed inside the canonical Ω-1 runtime path.

External models may later be used only as optional teachers for dataset generation, with provenance and contamination controls. They are never required for inference.

## 3. Core abstractions

### 3.1 GraphCard

A persistent node with:

- stable integer/string identity;
- node type;
- symbolic label;
- dense latent state;
- confidence;
- activation;
- importance;
- prediction error;
- consolidation strength;
- provenance;
- temporal metadata.

Initial node types:

`ENTITY`, `EVENT`, `ACTION`, `PROPERTY`, `RELATION`, `CLAIM`, `QUESTION`, `GOAL`, `RULE`, `CAUSE`, `EFFECT`, `TIME`, `PLACE`, `PERSON`, `MEMORY`, `HYPOTHESIS`, `CONTRADICTION`, `PLAN`, `WORD`, `MORPHEME`, `CONCEPT`, `ANSWER`.

### 3.2 TypedHyperEdge

A relation connecting one or more source nodes to one or more destination nodes, with:

- relation type;
- confidence;
- temporal validity;
- provenance;
- learned latent edge state.

The data model must support ordinary directed edges as a special case.

### 3.3 DynamicHyperGraph

Owns cards, edges, indexes, graph version, mutation log, and deterministic serialization.

Required mutation operations:

`CREATE`, `LINK`, `UNLINK`, `ACTIVATE`, `SUPPRESS`, `UPDATE`, `MERGE`, `RETRACT`.

Ω-1 V1 implements only operations that can be safely tested; the contract reserves future structural operators such as `SPLIT`.

### 3.4 ActiveWorkspace

A bounded induced subgraph selected from persistent memory and current input.

Default working-set target: 32–512 cards.

The workspace is the recurrent cognitive state. Long-term graph memory may be much larger than the workspace.

## 4. GraphScript

GraphScript is the canonical symbolic interchange representation for training fixtures, debugging, exact tests, and teacher traces.

Minimal V1 grammar:

```text
NODE <id> : <TYPE> ["label"]
EDGE <source> -> <target> : <RELATION> [CONF=<0..1>]
QUERY <relation>(<arg>)
ANSWER <node-or-literal>
```

Requirements:

- deterministic parser;
- deterministic formatter;
- parse(format(graph)) round-trip for supported constructs;
- explicit validation errors;
- no `eval`/dynamic code execution.

## 5. Russian Graph Compiler

V1 intentionally starts with a deterministic, inspectable compiler rather than pretending a tiny neural parser already understands unrestricted Russian.

Supported initial constructions:

- `<X> — это <Y>` / `<X> это <Y>`;
- `<X> является <Y>`;
- `<X> старше <Y>`;
- `<X> находится в <Y>`;
- `<X> принадлежит <Y>`;
- questions such as `Кто старше?`, `Где находится X?`, `Кому принадлежит X?`.

It produces graph nodes/edges and a query node. The compiler interface is replaceable by a learned graph parser later.

## 6. Recurrent Graph Cognition

The neural heart of Ω-1 is **GraphRecurrentCore**, operating on node and edge latent states over multiple cognitive steps.

At each step:

1. typed edge message projection;
2. source/destination aggregation;
3. gated node-state update;
4. global-workspace broadcast;
5. activation update;
6. optional structural proposal logits.

The V1 differentiable core must be implementable in plain PyTorch without requiring PyG/DGL, to minimize dependency and reproducibility risk.

The first structural proposal head predicts an operation distribution over:

`NOOP`, `ACTIVATE`, `SUPPRESS`, `LINK`, `RETRACT`, `ANSWER`.

The executor remains deterministic and policy-gated; raw neural logits never mutate persistent memory directly without validation.

## 7. Symbolic rule bridge

Ω-1 is hybrid graph-neural rather than dogmatically neural-only.

A small deterministic rule engine provides exact supervision and safe reasoning for initial capabilities, including transitive relations such as:

```text
older_than(A,B) & older_than(B,C) -> older_than(A,C)
```

Rules create derived edges with provenance `rule:<name>` and bounded confidence.

These traces become training data for GraphRecurrentCore and later learned structural mutation.

## 8. Memory

### Episodic memory

Stores individual graph events/claims with timestamps and provenance.

### Semantic memory

Stores consolidated concepts and high-confidence relations.

### Retrieval

V1 retrieval combines:

- exact label/type lookup;
- relation-neighborhood expansion;
- activation spreading;
- latent cosine similarity when embeddings are available.

No vector database is required for the first release.

### Consolidation

V1 implements deterministic duplicate merging and confidence accumulation. Learned sleep/consolidation is deferred until the base runtime is reproducible.

## 9. AnswerGraph

Reasoning never directly returns prose. It returns an `AnswerGraph` containing:

- answer node/value;
- supporting node IDs;
- supporting edge IDs;
- confidence;
- provenance;
- discourse intent.

The realizer may not change the semantic answer encoded in AnswerGraph.

## 10. Graph-to-Russian Realizer

V1 has two layers:

1. **DeterministicRussianRealizer** — exact templates + morphology-lite for benchmarkable correctness;
2. **NeuralGraphRealizer** — trainable graph-conditioned GRU decoder for free surface generation.

The neural realizer is explicitly **not an LLM**: it receives AnswerGraph/node states and learns surface Russian. It is not the reasoning authority.

For Ω-1 V1, deterministic realization is the canonical fallback and neural realization is experimental until semantic-preservation gates pass.

## 11. End-to-end GLLM interface

```python
class NexusGLLM:
    def learn(self, text: str) -> GraphUpdate: ...
    def ask(self, text: str) -> GLLMResponse: ...
    def save(self, path: str) -> None: ...
    @classmethod
    def load(cls, path: str) -> "NexusGLLM": ...
```

`GLLMResponse` contains:

- `text`;
- `answer_graph`;
- `workspace_trace` (safe structural trace, not hidden chain-of-thought);
- `confidence`.

## 12. Training objectives

The trainable model is multi-objective:

```text
L =
  λ_node * node_type_prediction
+ λ_edge * edge_relation_prediction
+ λ_transition * next_graph_state
+ λ_answer * answer_selection
+ λ_reconstruct * graph_reconstruction
+ λ_realize * graph_to_text
+ λ_conf * confidence_calibration
+ λ_sparse * workspace_sparsity
```

The first milestone trains only objectives for which supervised fixtures exist. No loss term may be reported unless it is actually computed.

## 13. Dataset format

Canonical JSONL record:

```json
{
  "id": "ru-transitive-000001",
  "input_text": "Антон старше Бориса. Борис старше Виктора.",
  "query_text": "Кто самый старший?",
  "graphscript": "...",
  "answer": "Антон",
  "task": "transitive_reasoning",
  "split": "train",
  "provenance": "synthetic:v1"
}
```

Train/dev/blind splits are frozen by manifest SHA before tuning on blind data.

## 14. V1 benchmarks

### Functional gates

- GraphScript round-trip: 100% on fixtures;
- graph persistence round-trip: 100%;
- no duplicate node IDs after mutation;
- exact rule inference: 100% on deterministic unit suite;
- AnswerGraph semantic preservation by deterministic realizer: 100%;
- end-to-end supported Russian micro-world QA: 100% on public dev fixtures.

### Blind research benchmark

At least 200 generated-but-frozen cases across:

- relation extraction;
- transitivity;
- containment/location;
- possession;
- contradiction/retraction;
- two-turn context;
- unseen entity names;
- graph persistence reload.

Blind generation seed, corpus SHA and raw outputs are recorded before model selection.

## 15. Repository layout

```text
src/nexus_gllm/
  schema.py
  graph.py
  graphscript.py
  compiler_ru.py
  workspace.py
  rules.py
  recurrent.py
  answer.py
  realizer_ru.py
  model.py
  persistence.py
training/
  dataset.py
  generate_synthetic.py
  train_core.py
  train_realizer.py
benchmarks/
  run_benchmark.py
  freeze_manifest.py
tests/
  test_graphscript.py
  test_graph.py
  test_rules.py
  test_end_to_end.py
  test_recurrent.py
  test_persistence.py
.github/workflows/ci.yml
pyproject.toml
README.md
```

## 16. Technical stack

- Python >= 3.11
- PyTorch >= 2.2
- standard library dataclasses/enums/json
- pytest >= 8
- no mandatory PyTorch Geometric, DGL, NetworkX, Transformers, or external LLM API

## 17. Security/reproducibility

- no dynamic code execution from GraphScript;
- deterministic IDs/seeds in tests;
- JSON serialization only for canonical graph state;
- model checkpoints use PyTorch state dicts plus explicit config/manifest;
- no pickle loading of untrusted external files in canonical CLI;
- every benchmark run records config, seed, git SHA, and artifact hashes when available.

## 18. What Ω-1 is not

- not `LLM + RAG`;
- not `LLM + knowledge graph`;
- not a wrapper around a commercial API;
- not a sequence Transformer with a graph prompt;
- not an AGI claim;
- not a promise that 20–50M parameters will immediately match frontier LLMs.

It is a falsifiable graph-native language/cognition architecture whose intelligence can be scaled by graph computation, persistent memory, learned dynamics and graph-to-language realization.
