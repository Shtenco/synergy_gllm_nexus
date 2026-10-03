# CRC SECOND POST-FREEZE BLIND VERDICT

## Frozen architecture

Authority cognitive architecture SHA:

`97a9c7ed12900969c68ba596e629c70adb398f06`

Freeze record commit:

`19dc756fe73c02327f623f3c66ad412a1a1d1e16`

The second-blind workflow verified before execution that `src/nexus_gllm/unified_v3/cognitive/` had not changed relative to the authority SHA.

## Historical boundary

The first frozen FAR-OOS result remains immutable:

- authority SHA: `6067746d3dbab7a5a0a7388545b73116fd23c25a`
- exact success: 85.71428571%
- `LONG_HORIZON_PLAN`: 0%
- verdict: `PARTIAL_TRANSFER`

That result was used only to diagnose the planning-depth defect. Its 672 scored cases were not reused as second-blind transfer evidence.

## Second blind execution

Evaluator/workflow HEAD:

`538d85c4b7b715a7021ddbd45c1803ff8f4aee6e`

GitHub Actions run:

`37143234492`

Evidence artifact:

- artifact id: `11280614978`
- name: `crc-second-blind-9300d1f4a359194060aaa88bc1e66758c11c9027`
- digest: `sha256:9692af0ab08b663d14d358176c88facfe0b7b4eb8f6ee85f34d54789438c18d4`

Protocol:

- 8 fresh seeded streams: `420001..420008`
- 10 repeats per stream
- 6 blind task families
- 480 scored cases
- planning horizons observed: 2, 3, 4, 5
- compute budget: 1.0 units/case
- first FAR-OOS cases reused: no
- independent oracle: yes
- M32-META opened: no
- FTX2 authored: no

## Results

| Metric | Result |
|---|---:|
| Exact task success | 0.8458333333 |
| Minimum family accuracy | 0.5000000000 |
| Credit leakage | 0.0 |
| Mean compute spent | 0.5333333333 |
| Max compute spent | 0.7000000000 |
| Success / compute | 1.5859375000 |
| Budget violations | 0 |
| Seed success std | 0.0246503324 |

### Family accuracy

| Blind family | Accuracy |
|---|---:|
| MEMORY_BRIDGE_NOISE | 1.000 |
| CAUSAL_CONFOUNDED_INTERVENTION | 0.575 |
| PLANNING_H2_H5 | 0.500 |
| PROGRAM_NESTED_NOVEL | 1.000 |
| CREDIT_MULTI_EPISODE | 1.000 |
| META_CALIBRATION_MIXED | 1.000 |

Per-seed exact success:

`[0.8833333333, 0.8666666667, 0.8333333333, 0.8666666667, 0.8000000000, 0.8333333333, 0.8333333333, 0.8500000000]`

## Pre-registered mechanical verdict

Rule fixed before execution:

- `TRANSFER_SUPPORTED` iff exact success >= 0.80 and every family >= 0.50;
- otherwise `PARTIAL_TRANSFER` iff exact success >= 0.50;
- otherwise `FAIL`.

Observed:

- exact success = `0.8458333333` >= `0.80`;
- minimum family accuracy = `0.50` >= `0.50`.

Therefore the mechanical verdict is:

`TRANSFER_SUPPORTED`

## Scientific interpretation

The second post-freeze blind battery provides stronger evidence that the cognitive mechanisms transfer beyond the controlled DEV benchmark and beyond the first FAR-OOS generator. The strongest observed transfer is in noisy grounded memory, nested program execution, multi-episode recursive credit and mixed meta-calibration, each at 100% in this battery.

The evidence is not uniform. Planning over horizons 2-5 is exactly at the acceptance floor (50%), and confounded/interventional causal reasoning is only 57.5%. Those are active capability boundaries and must not be hidden by the aggregate 84.58% score.

Accordingly, this run supports transfer of the frozen cognitive architecture under the stated battery. It does not establish universal intelligence, unrestricted real-world competence, or universal long-horizon planning.

## Seals

- `M32-META`: SEALED / UNOPENED
- `FTX2`: UNAUTHORED

No architecture change may retroactively alter this verdict. Any improvement motivated by the weak planning or causal families belongs to a later DEV cycle with a later fresh blind evaluation.
