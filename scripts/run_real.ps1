# Run the pipeline on REAL data on Windows, without needing `make`.
#
#   powershell -ExecutionPolicy Bypass -File scripts\run_real.ps1 -Fetch    # download, then build and check
#   powershell -ExecutionPolicy Bypass -File scripts\run_real.ps1           # rebuild from files already downloaded
#
# Downloads go to data\raw\ (gitignored). NSW data is CC BY-NC-ND 4.0: keep it, and anything
# built from it, on your own machine.
param(
    [switch]$Fetch,
    [int[]]$NswYears = @(2024, 2025)
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONPATH = 'src'

function Step($title, [scriptblock]$cmd) {
    Write-Host "`n=== $title ===" -ForegroundColor Cyan
    & $cmd
    if ($LASTEXITCODE -ne 0) { Write-Host "Stopped: '$title' failed (exit $LASTEXITCODE)." -ForegroundColor Red; exit $LASTEXITCODE }
}

if ($Fetch) {
    $years = $NswYears | ForEach-Object { "$_" }
    Step 'Download real data' { python -m oda.fetch --nsw-years @years --nsw-this-year --dft }
}

$env:DATA_MODE = 'real'
Step 'Build warehouse (real data)' { python -m oda.pipeline }
Step 'Data quality checks'         { python -m oda.quality }
Step 'Grounding evals'             { python evals/run_evals.py }
Step 'Market brief'                { python -m oda.insights }

Write-Host "`nDone. Brief: reports\insight_brief_real.md   Marts for Power BI: data\marts_real\" -ForegroundColor Green
