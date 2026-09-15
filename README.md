# NEXUS GLLM Ω-1 / Ω-1.1

**Graph Latent Language Model — graph-native cognition, persistent memory, temporal/causal world state and native Russian generation.**

NEXUS GLLM is not an ordinary LLM. The canonical runtime does **not** require Qwen, Llama, Mistral, GPT, Transformers, RAG, or an external LLM API.

Its primary cognitive state is a **dynamic typed hypergraph**. Russian text becomes validated graph structure, recurrent graph cognition operates on an active workspace, temporal/causal relations update a living world model, sleep consolidates memory, and the semantic result is represented as an `AnswerGraph` before Russian text is generated.

## Current architecture

```text
Russian text / events / persistent memory
                ↓
     Neural Russian→Graph Compiler
       + deterministic fallback
                ↓
       ProposalValidator / policy gate
                ↓
       Dynamic Typed Hypergraph
                ↓
   Temporal / Causal Event Graph
                ↓
        Active Graph Workspace
                ↓
      Recurrent Graph Cortex
                ↓
 rules + policy-gated structural proposals
                ↓
            AnswerGraph
                ↓
   Native Graph → Russian Decoder
                ↓
      semantic guard / fallback
                ↓
             Russian text

              + offline
                ↓
        Sleep / Consolidation
                ↓
 episodic evidence → stronger semantic memory
```

## What is implemented

### Graph-native runtime

- typed `GraphCard` memory nodes with latent state, confidence, activation, importance and provenance;
- `TypedHyperEdge` with confidence, latent state, consolidation metadata and provenance;
- persistent `DynamicHyperGraph`;
- versioned graph mutation and historical edge retraction;
- safe `GraphScript` parser/formatter;
- deterministic Russian micro-world graph compiler;
- exact transitive reasoning (`older_than`);
- living world-state revision for exclusive `owned_by` / `located_in` relations;
- bounded `ActiveWorkspace` retrieval;
- deterministic `GraphTensorizer`;
- trainable plain-PyTorch `GraphRecurrentCore`;
- recurrent cognition integrated into the live `NexusGLLM.ask()` path;
- policy-gated neural structural proposals;
- `AnswerGraph` semantic output contract;
- JSON persistent graph memory.

### Ω-1.1 Neural Russian → Graph Compiler

- `CompilerCharVocab` built from the training corpus, without external tokenizer dependency;
- character embeddings + bidirectional GRU semantic encoder;
- relation classification head;
- subject start/end pointer heads;
- object start/end pointer heads;
- confidence head;
- structured `NeuralParseProposal` contract;
- `ProposalValidator` with relation allow-list, exact span validation, confidence thresholds and self-loop protection;
- explicit `abstain` relation;
- compiler checkpoint save/load with architecture config, vocab, relation vocab, seed and manifest SHA;
- validated neural compiler integrated into `NexusGLLM.learn()`;
- deterministic compiler remains fallback when the neural proposal is rejected or abstains.

The central safety invariant is:

> **The neural compiler may propose meaning; only validated graph operations may become persistent memory.**

### Temporal / causal world graph

- `EVENT` nodes;
- `before` / canonicalized `after` relations;
- `causes` relations;
- actor/object relation helpers;
- multi-hop temporal reachability;
- multi-hop causal ancestry;
- strict cycle rejection for temporal/causal DAGs;
- retraction-aware traversal;
- auditable support-edge traces;
- optional materialized temporal and causal closure;
- deterministic Russian supervision fixtures:
  - `Сначала A, потом B.`
  - `A, поэтому B.`
  - `После A произошло B.`
  - `Что было раньше: A или B?`
  - `Что стало причиной B?`
- temporal/causal QA is integrated into public `NexusGLLM.ask()`.

### Sleep / consolidation

`NexusGLLM.sleep()` executes a deterministic, non-destructive consolidation pass:

1. duplicate node normalization and edge rewiring;
2. repeated-edge evidence accumulation using `1 - Π(1-c_i)`;
3. exclusive-state conflict cleanup while preserving historical edges;
4. consolidation-strength updates;
5. semantic promotion to `sleep:semantic` provenance;
6. versioned mutation-log records for merge/update/retract actions.

Ω-1.1 does **not** physically delete memory during sleep. Forgetting/decay remains deferred until a protected-fact benchmark exists.

### Native Russian output

- deterministic Russian fallback realizer;
- native graph-conditioned GRU Russian decoder trained from scratch;
- bounded autoregressive generation;
- semantic guard: neural prose is rejected if it loses the protected `AnswerGraph.answer_value`;
- recurrent-core and Russian-realizer checkpoint loading.

## Install

Python 3.11+:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

## Minimal graph-native inference

```python
from nexus_gllm import NexusGLLM

nexus = NexusGLLM(neural_seed=17)
nexus.learn("Антон старше Бориса")
nexus.learn("Борис старше Виктора")

response = nexus.ask("Кто самый старший?")
print(response.text)
print(response.cognition_logits)
```

## Temporal / causal example

```python
nexus = NexusGLLM()

nexus.learn("Сначала дождь начался, потом канава переполнилась.")
nexus.learn("Канава переполнилась, поэтому дорогу затопило.")

print(nexus.ask("Что было раньше: дождь начался или канава переполнилась?").text)
print(nexus.ask("Что стало причиной дорогу затопило?").text)
```

## Sleep example

```python
report = nexus.sleep()
print(report)
```

The graph is consolidated without physical deletion of episodic history.

## Generate the Ω-1 graph-cortex corpus

```bash
python -m training.generate_synthetic \
  --out data/omega1_synthetic.jsonl \
  --seed 17 \
  --train 1000 \
  --dev 200 \
  --blind 200
```

## Generate the Ω-1.1 neural-compiler corpus

```bash
python -m training.generate_compiler_corpus \
  --out data/omega1_1_compiler.jsonl \
  --seed 17 \
  --train 4000 \
  --dev 800 \
  --blind 800
```

Compiler task families include:

- `older_than`;
- `located_in`;
- `owned_by`;
- `is_a`;
- `before`;
- `causes`;
- `world_revision`;
- `abstain`.

Train/dev/blind use distinct entity namespaces **and distinct surface templates**. Template hashes are written into the manifest.

## Train the neural Russian→Graph compiler

```bash
python -m training.train_compiler \
  data/omega1_1_compiler.jsonl \
  --out checkpoints/omega1_1_compiler.pt \
  --epochs 4 \
  --seed 17
```

Load it:

```python
nexus = NexusGLLM()
nexus.load_compiler_checkpoint("checkpoints/omega1_1_compiler.pt")
nexus.learn("Антон старше Бориса")
```

The compiler checkpoint never receives direct authority over memory. `ProposalValidator` remains in the runtime path.

## Train the recurrent graph cortex

```bash
python -m training.train_core \
  data/omega1_synthetic.jsonl \
  --out checkpoints/omega1_core.pt \
  --epochs 3 \
  --seed 17
```

## Train the native Graph→Russian decoder

```bash
python -m training.train_realizer \
  data/omega1_synthetic.jsonl \
  --out checkpoints/omega1_realizer.pt \
  --epochs 4 \
  --seed 17
```

## Freeze before evaluation

```bash
python -m benchmarks.freeze_manifest data/omega1_synthetic.jsonl --seed 17
```

Never edit a frozen blind artifact after observing results.

## Benchmarks

### Recurrent graph cortex

```bash
python -m benchmarks.run_benchmark \
  data/omega1_synthetic.jsonl \
  --split blind \
  --core-checkpoint checkpoints/omega1_core.pt \
  --out results/omega1_blind.json
```

### Neural Russian→Graph compiler

```bash
python -m benchmarks.run_compiler_benchmark \
  data/omega1_1_compiler.jsonl \
  checkpoints/omega1_1_compiler.pt \
  --split blind \
  --out results/omega1_1_compiler_blind.json
```

Metrics include relation accuracy, subject/object exact spans, strict structural exact match, invalid accepted proposal rate, and abstention precision/recall.

### Temporal / causal smoke suite

```bash
python -m benchmarks.run_temporal_benchmark \
  --out results/omega1_1_temporal.json
```

### Sleep / consolidation smoke suite

```bash
python -m benchmarks.run_consolidation_benchmark \
  --out results/omega1_1_consolidation.json
```

These internal synthetic suites are engineering benchmarks only. A high score is **not** an AGI or external SOTA claim.

## Tests

```bash
pytest -q
python -m compileall src training benchmarks
```

## Architecture documents

- `docs/superpowers/specs/2026-09-15-nexus-gllm-omega1-design.md`
- `docs/superpowers/specs/2026-09-15-omega1-neural-compiler-temporal-sleep-design.md`
- `docs/superpowers/plans/2026-09-15-nexus-gllm-omega1-implementation.md`
- `docs/superpowers/plans/2026-09-15-omega1-neural-compiler-temporal-sleep.md`
- `ARCHITECTURE.md`
- `PROVENANCE.md`

## Current research boundary

Ω-1.1 now contains a trainable Russian→Graph compiler, graph-native recurrent cognition, temporal/causal world-state reasoning, persistent memory consolidation, and a native Russian graph-conditioned decoder.

It still does **not** claim unrestricted Russian understanding. Current compiler supervision is structured and synthetic; before promotion to a general compiler it must pass frozen blind suites with template-disjoint paraphrases and then external human-written Russian evaluation.

The next major research objective is scaling from synthetic relation/event supervision to **large heterogeneous Russian graph pretraining**, followed by belief/contradiction dynamics, learned consolidation, continual-learning gates and larger Ω-2/Ω-3 graph cortex generations.
