# NEXUS local validation snapshot

This branch is a downloadable local snapshot of the current NEXUS experimental system.

Snapshot ancestry before local-run helper files:

`21c0c9679b407b52d6df4a08aba5038b5c401930`

Branch:

`nexus-local-run-2026-10-09`

The branch contains the full repository state at that experimental snapshot plus only local-run helper files.

## Requirements

- Git
- Python 3.11 recommended
- Windows PowerShell 5+ or PowerShell 7, or Bash on Linux/macOS
- Internet access for the first dependency install

## Clone

```bash
git clone --branch nexus-local-run-2026-10-09 --single-branch https://github.com/Shtenco/synergy_gllm_nexus.git
cd synergy_gllm_nexus
```

The repository is private, so GitHub authentication is required.

## Windows

Focused Planning + Causal DEV/regressions plus benchmark artifacts:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local_validation.ps1
```

Full repository gate:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local_validation.ps1 -Full
```

After the first install, you may skip installation:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local_validation.ps1 -Full -SkipInstall
```

## Linux / macOS

```bash
bash scripts/run_local_validation.sh
```

Full repository gate:

```bash
bash scripts/run_local_validation.sh --full
```

After the first install:

```bash
bash scripts/run_local_validation.sh --full --skip-install
```

## Focused validation executed by the launcher

The launcher runs:

- post-second-blind planning budget contracts;
- full-loop H8 planning;
- signed causal contracts;
- historical planning and causal regressions;
- Planning H2-H8 DEV;
- independent random SCM DEV;
- Wilson statistics reference tests;
- focused compileall.

The `--full` / `-Full` mode additionally executes:

```text
pytest -q
python -m compileall src training benchmarks
```

## Produced evidence

The DEV launchers write:

- `artifacts/crc_planning_causal_dev.json`
- `artifacts/crc_scm_dev.json`

Please preserve the full console output if a test fails.

## Research seals

This local snapshot does not alter the research protocol:

- historical blind verdicts remain immutable;
- M32-META remains sealed/unopened;
- FTX2 remains unauthored;
- the Third Blind generator/corpus remains unauthored;
- a new commit-bound freeze must not be declared until the required DEV/regression/full-CI-equivalent execution is genuinely GREEN.

A successful local run is valuable execution evidence, but it must be recorded separately from GitHub-hosted Actions evidence.
