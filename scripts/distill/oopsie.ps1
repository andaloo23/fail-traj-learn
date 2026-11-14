param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('verify','collect-smoke','collect','review','export','audit','smoke','train')]
  [string]$Action,
  [string]$Run = 'outputs/oopsie_distillation_md_v2',
  [string]$Data = 'outputs/oopsie_sft_md_sol_v2',
  [double]$BudgetUsd = 30
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$py = Join-Path $repo '.venv-oopsie-distill/Scripts/python.exe'
$env:PYTHONUNBUFFERED = '1'
$env:PYTHONIOENCODING = 'utf-8'
Push-Location $repo
try {
  switch ($Action) {
    'verify' { & $py scripts/distill/oopsie_pipeline.py verify --run $Run }
    'collect-smoke' { & $py scripts/distill/oopsie_pipeline.py collect --run $Run --budget-usd $BudgetUsd --episodes O001 --limit 2 }
    'collect' { & $py scripts/distill/oopsie_pipeline.py collect --run $Run --budget-usd $BudgetUsd }
    'review' { & $py scripts/distill/oopsie_pipeline.py review --run $Run }
    'export' { & $py scripts/distill/oopsie_pipeline.py export --run $Run --out $Data --teacher sol }
    'audit' { & $py scripts/distill/qwen_oopsie_sft.py audit --data $Data }
    'smoke' { & $py scripts/distill/qwen_oopsie_sft.py train --data $Data --out outputs/oopsie_qwen7b_md_smoke_v2 --max-steps 1 --max-hours 1 }
    'train' { & $py scripts/distill/qwen_oopsie_sft.py train --data $Data --out outputs/oopsie_qwen7b_md_sft_v2 --max-hours 5 }
  }
  if ($LASTEXITCODE -ne 0) { throw "OopsieData command failed with exit code $LASTEXITCODE" }
} finally { Pop-Location }
