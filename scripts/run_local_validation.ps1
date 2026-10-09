param(
    [switch]$Full,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

$Venv = Join-Path $Root ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host "==> Creating Python 3.11 virtual environment"
    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($PyLauncher) {
        & py -3.11 -m venv $Venv
    } else {
        & python -m venv $Venv
    }
}

if (-not $SkipInstall) {
    Write-Host "==> Installing NEXUS + DEV dependencies"
    & $Python -m pip install --upgrade pip
    & $Python -m pip install -e ".[dev]"
}

$Focused = @(
    "tests/crc_r1/test_post_second_blind_planning_budget.py",
    "tests/crc_r1/test_post_second_blind_cognitive_loop_planning.py",
    "tests/crc_r1/test_post_second_blind_signed_causal.py",
    "tests/crc_r1/test_post_far_oos_planning_depth.py",
    "tests/crc_r1/test_learned_future.py",
    "tests/crc_r1/test_causal_model.py",
    "tests/crc_r1/test_cognitive_causal_integration.py",
    "tests/crc_r1/test_planning_causal_dev_benchmark.py",
    "tests/crc_r1/test_crc_statistics.py",
    "tests/crc_r1/test_crc_scm_oracle.py",
    "tests/crc_r1/test_crc_scm_dev.py"
)

Write-Host "==> Focused Planning + Causal DEV / regressions"
& $Python -m pytest -q @Focused

New-Item -ItemType Directory -Force -Path (Join-Path $Root "artifacts") | Out-Null

Write-Host "==> Stratified Planning H2-H8 + signed causal DEV"
& $Python -m benchmarks.crc_planning_causal_dev.run --seed 20261003 --out artifacts/crc_planning_causal_dev.json

Write-Host "==> Independent random SCM DEV"
& $Python -m benchmarks.crc_scm_dev.run --seed 2026100303 --cases-per-regime 70 --out artifacts/crc_scm_dev.json

Write-Host "==> Compile focused cognitive/benchmark surface"
& $Python -m compileall src/nexus_gllm/unified_v3/cognitive benchmarks/crc_planning_causal_dev benchmarks/crc_scm_dev benchmarks/crc_statistics.py benchmarks/crc_scm_oracle.py

if ($Full) {
    Write-Host "==> FULL repository pytest"
    & $Python -m pytest -q
    Write-Host "==> FULL compileall"
    & $Python -m compileall src training benchmarks
}

Write-Host ""
Write-Host "NEXUS LOCAL VALIDATION COMPLETED."
Write-Host "Artifacts:"
Write-Host "  artifacts/crc_planning_causal_dev.json"
Write-Host "  artifacts/crc_scm_dev.json"
if (-not $Full) {
    Write-Host "Run again with -Full for the full repository pytest + compileall gate."
}
