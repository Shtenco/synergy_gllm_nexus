# NEXUS GLLM Ω-1

**Graph Latent Language Model — graph-native cognition, persistent memory and native Russian generation.**

NEXUS GLLM Ω-1 is not an ordinary LLM. The canonical runtime does **not** require Qwen, Llama, Mistral, GPT, Transformers, RAG, or an external LLM API.

Its primary cognitive state is a **dynamic typed hypergraph**. Text is compiled into graph structure, reasoning happens over active graph state, the trainable recurrent graph cortex processes that state, and the semantic result is represented as an `AnswerGraph` before Russian text is generated.

## Core idea

```text
Russian text / events / persistent memory
                ↓
        Russian Graph Compiler
                ↓
       Dynamic Typed Hypergraph
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
```

## What is implemented

- typed `GraphCard` memory nodes with latent state, confidence, activation, importance and provenance;
- `TypedHyperEdge` plus persistent `DynamicHyperGraph`;
- versioned graph mutation and historical edge retraction;
- safe `GraphScript` parser/formatter;
- deterministic Russian micro-world graph compiler;
- exact transitive reasoning (`older_than`);
- living world-state revision for exclusive `owned_by` / `located_in` relations;
- bounded `ActiveWorkspace` retrieval;
- deterministic `GraphTensorizer`;
- trainable plain-PyTorch `GraphRecurrentCore` with typed messages, global workspace broadcast and recurrent updates;
- recurrent cognition is integrated into the live `NexusGLLM.ask()` path;
- policy-gated neural structural proposals: `LINK`, `RETRACT`, `ACTIVATE`, `SUPPRESS`;
- `AnswerGraph` semantic output contract;
- deterministic Russian fallback realizer;
- **native graph-conditioned GRU Russian decoder trained from scratch** — not a pretrained LLM;
- bounded autoregressive generation for the native decoder;
- semantic guard: neural prose is rejected if it loses the protected `AnswerGraph.answer_value`;
- recurrent-core and Russian-realizer checkpoint loading;
- JSON persistent graph memory;
- reproducible multi-task synthetic graph corpus;
- disjoint train/dev/blind entity namespaces and SHA-256 manifests;
- native recurrent-cortex trainer;
- native Graph→Russian decoder trainer;
- benchmark freeze manifest and per-task blind benchmark runner;
- architecture/provenance/evidence documentation.

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
# Самый старший — Антон.

print(response.cognition_logits)
# six recurrent graph-operation logits from the active workspace
```

## Living world state

```python
nexus = NexusGLLM()
nexus.learn("Автомобиль принадлежит Антону")
nexus.learn("Автомобиль принадлежит Борису")

print(nexus.ask("Кому принадлежит Автомобиль?").text)
# Принадлежит: Борис.
```

The second exclusive world fact retracts the old active `owned_by` edge while preserving history.

## GraphScript

```text
NODE anton : PERSON ["Антон"]
NODE boris : PERSON ["Борис"]
NODE victor : PERSON ["Виктор"]
EDGE anton -> boris : older_than CONF=1.0
EDGE boris -> victor : older_than CONF=1.0
QUERY oldest(?)
ANSWER anton
```

GraphScript is data, not executable code.

## Generate the Ω-1 multi-task corpus

```bash
python -m training.generate_synthetic \
  --out data/omega1_synthetic.jsonl \
  --seed 17 \
  --train 1000 \
  --dev 200 \
  --blind 200
```

Current task families include:

- `transitive_reasoning`;
- `location_lookup`;
- `ownership_lookup`;
- `world_revision`.

The recurrent operation target distinguishes at least `ANSWER` and `RETRACT` rather than teaching a one-class dummy policy.

## Freeze before evaluation

```bash
python -m benchmarks.freeze_manifest data/omega1_synthetic.jsonl --seed 17
```

Never edit a frozen blind artifact after observing results.

## Train the recurrent graph cortex

```bash
python -m training.train_core \
  data/omega1_synthetic.jsonl \
  --out checkpoints/omega1_core.pt \
  --epochs 3 \
  --seed 17
```

Load it into the runtime:

```python
nexus = NexusGLLM()
nexus.load_core_checkpoint("checkpoints/omega1_core.pt")
```

## Train the native Graph→Russian decoder

```bash
python -m training.train_realizer \
  data/omega1_synthetic.jsonl \
  --out checkpoints/omega1_realizer.pt \
  --epochs 4 \
  --seed 17
```

Use it with semantic protection:

```python
nexus.load_realizer_checkpoint("checkpoints/omega1_realizer.pt")
response = nexus.ask("Кто самый старший?", prefer_neural_realizer=True)
print(response.realizer_mode)
# neural_guarded OR deterministic_fallback
```

The learned decoder is accepted only when it preserves the semantic answer. Otherwise Ω-1 falls back to the deterministic realizer.

## Blind benchmark

```bash
python -m benchmarks.run_benchmark \
  data/omega1_synthetic.jsonl \
  --split blind \
  --core-checkpoint checkpoints/omega1_core.pt \
  --out results/omega1_blind.json
```

Results are emitted both globally and per task. The current benchmark is a deliberately narrow synthetic graph micro-world; even 100% would **not** mean AGI or external SOTA.

## Tests

```bash
pytest -q
python -m compileall src training benchmarks
```

## Architecture documents

- `docs/superpowers/specs/2026-09-15-nexus-gllm-omega1-design.md`
- `docs/superpowers/plans/2026-09-15-nexus-gllm-omega1-implementation.md`
- `ARCHITECTURE.md`
- `PROVENANCE.md`

## Current research boundary

Ω-1 already has a graph-native cognitive/runtime path and two native trainable neural organs, but it does **not** yet claim unrestricted Russian understanding. The current text→graph compiler is deliberately narrow and inspectable. Learned persistent structural mutation remains behind a deterministic policy gate.

The next major research objective is a **learned Russian text→dynamic-graph compiler**, followed by richer temporal/causal graphs, contradiction/belief dynamics, consolidation (“sleep”), and larger Ω-2/Ω-3 graph cortex generations.
