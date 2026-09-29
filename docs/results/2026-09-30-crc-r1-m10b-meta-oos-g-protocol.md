# CRC-R1 M10b — META-OOS G Integrated Cognitive Loop Protocol

**Date:** 2026-09-30

META-OOS G is the first fresh benchmark aimed at the integrated CRC loop rather than one component at a time.

## Runtime phase

Each case supplies only:
- typed world facts;
- task;
- never-fixed higher-order AST;
- temporal ledger;
- memory events/tags;
- learned-world-model observations;
- planning state;
- novelty/uncertainty;
- predicted outcome reward.

It does **not** supply expected execution truth/status, optimal first action, minimum memory success or observed task reward.

## Scorer-only phase

Gold remains separate until every decision is serialized. It contains:
- expected execution status/truth;
- optimal first action;
- minimum memory retrieval count;
- observed task reward.

Only after decisions are frozen is gold opened once. Reward is then fed back as an observation for RPE/credit learning. It cannot influence the already-scored decision.

## Metrics

No single opaque score is used alone. The protocol reports:
- strict integrated accuracy;
- execution accuracy;
- planning accuracy;
- memory retrieval success;
- trace completeness;
- per-stratum strict accuracy.

## Boundaries

META-OOS G is internal typed research, not an AGI benchmark. It does not test natural-language parsing or external action. Its purpose is to falsify integration errors between memory, metacontrol, higher-order execution, planning and post-decision recursive credit.

FTX1 remains sealed and HARD-OOS D is not reused.
