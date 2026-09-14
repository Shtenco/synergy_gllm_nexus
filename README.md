# NEXUS GLLM Ω-1

**Graph Latent Language Model — graph-native cognition, memory and Russian language runtime.**

NEXUS GLLM Ω-1 is not an ordinary LLM and does not require Qwen, Llama, Mistral, GPT, Transformers, RAG, or an external LLM API inside its canonical runtime.

Its primary cognitive state is a **dynamic typed hypergraph**. Text is compiled into graph structure, reasoning happens over graph state, and the result is converted back to Russian through an AnswerGraph realizer.

## Core idea

```text
Russian text / memory / world state
        ↓
   Graph Compiler
        ↓
 Dynamic Typed Hypergraph
        ↓
 Active Cognitive Workspace
        ↓
 Recurrent Graph Cognition
        ↓
 Rules / structural proposals
        ↓
     AnswerGraph
        ↓
 Graph → Russian Realizer
        ↓
      Russian text
```

The neural core predicts and transforms graph state. Persistent memory remains auditable and deterministic until a learned structural policy passes explicit safety and benchmark gates.

## What is already implemented

- `GraphCard` typed memory nodes with confidence, activation, importance, provenance and latent state;
- `TypedHyperEdge` relations with provenance and confidence;
- `DynamicHyperGraph` with versioned mutations and retraction;
- safe `GraphScript` parser/formatter;
- deterministic Russian micro-world compiler;
- transitive graph reasoning (`older_than`);
- world-state revision for exclusive relations (`owned_by`, `located_in`);
- bounded `ActiveWorkspace` retrieval;
- trainable recurrent graph cognition core in plain PyTorch;
- operation logits for future structural graph actions;
- `AnswerGraph` as semantic output contract;
- deterministic Russian realizer;
- experimental graph-conditioned GRU realizer — not an LLM;
- JSON persistent graph memory;
- synthetic graph reasoning dataset generator;
- train/dev/blind split manifest hashing;
- recurrent-core training CLI;
- benchmark freeze manifest;
- blind benchmark runner;
- GitHub Actions test workflow;
- architecture spec and implementation plan.

## Install

Python 3.11+ is required.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

## Minimal example

```python
from nexus_gllm import NexusGLLM

nexus = NexusGLLM()

nexus.learn("Антон старше Бориса")
nexus.learn("Борис старше Виктора")

response = nexus.ask("Кто самый старший?")
print(response.text)
# Самый старший — Антон.
```

### Living world state

```python
nexus = NexusGLLM()

nexus.learn("Автомобиль принадлежит Антону")
print(nexus.ask("Кому принадлежит Автомобиль?").text)

nexus.learn("Автомобиль принадлежит Борису")
print(nexus.ask("Кому принадлежит Автомобиль?").text)
```

The second ownership fact retracts the previous active `owned_by` edge. NEXUS therefore maintains a changing world model instead of accumulating mutually active facts indefinitely.

## GraphScript

GraphScript is the inspectable intermediate language of Ω-1.

```text
NODE anton : PERSON ["Антон"]
NODE boris : PERSON ["Борис"]
NODE victor : PERSON ["Виктор"]

EDGE anton -> boris : older_than CONF=1.0
EDGE boris -> victor : older_than CONF=1.0

QUERY oldest(?)
ANSWER anton
```

GraphScript never executes Python or arbitrary code.

## Generate a reproducible training corpus

```bash
python -m training.generate_synthetic \
  --out data/omega1_synthetic.jsonl \
  --seed 17 \
  --train 1000 \
  --dev 200 \
  --blind 200
```

The generator creates disjoint entity pools for train/dev/blind and writes a SHA-256 manifest next to the JSONL file.

## Freeze the benchmark

```bash
python -m benchmarks.freeze_manifest data/omega1_synthetic.jsonl --seed 17
```

Once a blind corpus is frozen, it must not be edited to improve a score.

## Train the recurrent graph core

```bash
python -m training.train_core \
  data/omega1_synthetic.jsonl \
  --out checkpoints/omega1_core.pt \
  --epochs 3 \
  --seed 17
```

This trains the native `GraphRecurrentCore`. No pretrained language model is loaded.

## Run the blind benchmark

```bash
python -m benchmarks.run_benchmark \
  data/omega1_synthetic.jsonl \
  --split blind \
  --out results/omega1_blind.json
```

The current benchmark intentionally measures a narrow graph-reasoning micro-world. A 100% result on this synthetic benchmark is **not** an AGI, general-language or external SOTA claim.

## Tests

```bash
pytest -q
python -m compileall src training benchmarks
```

## Architecture files

- design: `docs/superpowers/specs/2026-09-15-nexus-gllm-omega1-design.md`
- implementation plan: `docs/superpowers/plans/2026-09-15-nexus-gllm-omega1-implementation.md`
- architecture overview: `ARCHITECTURE.md`
- provenance and evidence policy: `PROVENANCE.md`

## Research roadmap

Ω-1 deliberately begins with a narrow, falsifiable system. The next research stages are:

1. learned text → graph parsing;
2. learned structural mutation from recurrent graph state;
3. larger persistent memory with activation-based retrieval;
4. contradiction detection and belief confidence;
5. temporal/event graphs;
6. causal/world-model training;
7. learned graph consolidation (“sleep”);
8. richer Russian graph-to-text generation;
9. multi-task graph pretraining;
10. larger Ω-2 / Ω-3 graph cortex generations.

## Non-goals / current limitations

Ω-1 currently does **not** claim unrestricted Russian understanding. The deterministic compiler supports a small auditable set of constructions. The neural recurrent core is trainable but is not yet allowed to mutate long-term memory without deterministic validation.

This repository is an R&D system for a new graph-native model family. Claims must always be tied to exact benchmark artifacts, seeds and commits.
