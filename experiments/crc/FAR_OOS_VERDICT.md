# CRC FAR-OOS VERDICT

## Frozen architecture

Authority architecture SHA:

`6067746d3dbab7a5a0a7388545b73116fd23c25a`

The FAR-OOS workflow independently verified that `src/nexus_gllm/unified_v3/cognitive/` had not changed after this freeze before evaluation.

## Evaluator execution

Evaluator/workflow HEAD:

`9dd73153006cd5da466c6c111cc109fbec256318`

GitHub Actions run:

`37137817657`

Evidence artifact:

- artifact id: `11278987004`
- name: `crc-far-oos-6052adcc34755c5566aae05f0dd7e5efdd7f9fce`
- digest: `sha256:376aa4fde1bd93e671ea35a30e492519474f0dd8b5d0ff58a7fbf352a8049679`

Protocol:

- 8 seeded FAR-OOS streams
- 12 repeats per stream
- 7 held-out task families
- 672 scored cases
- compute budget: 1.0 units/case
- controlled DEV generator reused: no
- M32-META opened: no
- FTX2 authored: no

## Results

| Metric | Result |
|---|---:|
| Exact task success | 0.8571428571 |
| Proof complete rate | 1.0 |
| Causal accuracy | 1.0 |
| Planning accuracy | 0.0 |
| Post-feedback transfer | 1.0 |
| Calibrated abstention | 1.0 |
| Credit leakage | 0.0 |
| Mean compute spent | 0.5071428571 |
| Max compute spent | 0.7000000000 |
| Success / compute | 1.6901408451 |
| Budget violations | 0 |
| Seed success std | 0.0 |

### Family accuracy

| FAR-OOS family | Accuracy |
|---|---:|
| MEMORY_CHAIN_RU | 1.0 |
| TEMPORAL_SNAPSHOT | 1.0 |
| CAUSAL_REVERSAL | 1.0 |
| LONG_HORIZON_PLAN | **0.0** |
| CREDIT_TRANSFER | 1.0 |
| UNSEEN_COMPOSITION | 1.0 |
| CALIBRATED_ABSTENTION | 1.0 |

## Mechanical verdict

The pre-registered evaluator rule was:

- `TRANSFER_SUPPORTED` only if exact success >= 0.80 **and** every family >= 0.50;
- `PARTIAL_TRANSFER` if exact success >= 0.50 but the stronger rule is not met;
- otherwise `FAIL`.

Observed exact success was 0.8571428571, but `LONG_HORIZON_PLAN=0.0`. Therefore:

`PARTIAL_TRANSFER`

This verdict is intentionally preserved rather than tuning the frozen architecture after seeing FAR-OOS results.

## Scientific interpretation

The frozen cognitive architecture shows transfer on six held-out capability families: grounded memory chaining with Russian identifiers, temporal snapshots, intervention/counterfactual causal reversal, post-feedback responsibility transfer, unseen program composition, and calibrated abstention. The current evidence does **not** support robust long-horizon planning transfer: that family failed on every scored instance.

Accordingly, this run supports **partial cross-instance/cross-schema transfer**, not universal transfer and not a claim of general intelligence.

## Seals remain intact

- `M32-META`: SEALED / UNOPENED
- `FTX2`: UNAUTHORED

Any future architecture change prompted by the planning failure must be treated as a new development cycle and cannot retroactively change this FAR-OOS verdict.
