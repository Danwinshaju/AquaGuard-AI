$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$backendEnvironment = Join-Path $projectRoot "backend\.env"
$backendEnvironmentExample = Join-Path $projectRoot "backend\.env.example"

Write-Host "AquaGuard AI setup" -ForegroundColor Cyan
Write-Host "Project: $projectRoot"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating the Python 3.11 virtual environment..." -ForegroundColor Yellow
    & py -3.11 -m venv (Join-Path $projectRoot ".venv")
}

$env:PYTHONIOENCODING = "utf-8"

Write-Host "Updating pip..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip

Write-Host "Installing official CPU-only PyTorch..." -ForegroundColor Yellow
& $venvPython -m pip install `
    torch==2.7.1 `
    torchvision==0.22.1 `
    --index-url https://download.pytorch.org/whl/cpu

Write-Host "Installing AquaGuard backend packages..." -ForegroundColor Yellow
& $venvPython -m pip install -r (Join-Path $projectRoot "backend\requirements-dev.txt")

if (-not (Test-Path $backendEnvironment)) {
    Copy-Item -LiteralPath $backendEnvironmentExample -Destination $backendEnvironment
    Write-Host "Created backend/.env from the safe example." -ForegroundColor Green
}

Write-Host "Starting MongoDB..." -ForegroundColor Yellow
& docker compose --project-directory $projectRoot up -d mongodb

Write-Host "Checking installed AI packages..." -ForegroundColor Yellow
& $venvPython -c "import torch, ultralytics; print('PyTorch:', torch.__version__); print('Ultralytics:', ultralytics.__version__)"

Write-Host "Setup completed successfully." -ForegroundColor Green
Write-Host "Run the backend with:"
Write-Host ".\.venv\Scripts\Activate.ps1"
Write-Host "cd .\backend"
Write-Host "python -m uvicorn app.main:app --reload"
