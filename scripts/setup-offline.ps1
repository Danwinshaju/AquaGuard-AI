$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$offlineDirectory = Join-Path $projectRoot "offline"
$wheelDirectory = Join-Path $offlineDirectory "python-wheels"
$pythonInstaller = Join-Path $offlineDirectory "installers\python-3.11.9-amd64.exe"
$dockerInstaller = Join-Path $offlineDirectory "installers\Docker Desktop Installer.exe"
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

function Find-Python311 {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.11 --version *> $null
        if ($LASTEXITCODE -eq 0) {
            return @("py", "-3.11")
        }
    }
    $localPython = Join-Path $env:LocalAppData "Programs\Python\Python311\python.exe"
    if (Test-Path -LiteralPath $localPython) {
        return @($localPython)
    }
    return @()
}

Write-Host "AquaGuard offline setup" -ForegroundColor Cyan
Write-Host "Project: $projectRoot"

$pythonCommand = @(Find-Python311)
if ($pythonCommand.Count -eq 0) {
    if (-not (Test-Path -LiteralPath $pythonInstaller)) {
        throw "Python 3.11 is missing and its offline installer was not included."
    }
    Write-Host "Installing Python 3.11 for the current Windows user..." -ForegroundColor Yellow
    Start-Process -FilePath $pythonInstaller -Wait -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0"
    $pythonCommand = @(Find-Python311)
    if ($pythonCommand.Count -eq 0) {
        throw "Python installation finished but Python 3.11 could not be located. Restart Windows, then run this setup again."
    }
}

if (-not (Test-Path -LiteralPath $wheelDirectory)) {
    throw "Offline Python wheels are missing: $wheelDirectory"
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "Creating the portable project's virtual environment..." -ForegroundColor Yellow
    if ($pythonCommand.Count -eq 2) {
        & $pythonCommand[0] $pythonCommand[1] -m venv (Join-Path $projectRoot ".venv")
    }
    else {
        & $pythonCommand[0] -m venv (Join-Path $projectRoot ".venv")
    }
    if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed." }
}

Write-Host "Installing Python packages only from the pendrive files..." -ForegroundColor Yellow
& $venvPython -m pip install `
    --no-index `
    --find-links $wheelDirectory `
    --requirement (Join-Path $projectRoot "backend\requirements-dev.txt")
if ($LASTEXITCODE -ne 0) { throw "Offline Python package installation failed." }

$environmentFile = Join-Path $projectRoot "backend\.env"
if (-not (Test-Path -LiteralPath $environmentFile)) {
    Copy-Item `
        -LiteralPath (Join-Path $projectRoot "backend\.env.example") `
        -Destination $environmentFile
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    if (-not (Test-Path -LiteralPath $dockerInstaller)) {
        throw "Docker Desktop is missing and its offline installer was not included."
    }
    Write-Host "Installing Docker Desktop. WSL 2 and hardware virtualization must already be enabled." -ForegroundColor Yellow
    Start-Process -FilePath $dockerInstaller -Wait -ArgumentList "install", "--user"
    Write-Host "Docker Desktop was installed. Restart Windows, open Docker Desktop once, then run this setup again." -ForegroundColor Cyan
    exit 0
}

Write-Host "Loading the offline MongoDB image..." -ForegroundColor Yellow
& docker image inspect mongo:8.0 *> $null
if ($LASTEXITCODE -ne 0) {
    & docker image load --input (Join-Path $offlineDirectory "mongo-8.0.tar")
    if ($LASTEXITCODE -ne 0) { throw "MongoDB image loading failed. Make sure Docker Desktop is running." }
}

Write-Host ""
Write-Host "Offline setup is complete." -ForegroundColor Green
Write-Host "Run: powershell -ExecutionPolicy Bypass -File .\scripts\start-offline.ps1"
