param(
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$frontendDirectory = Join-Path $projectRoot "frontend"
$backendDirectory = Join-Path $projectRoot "backend"
$pythonExecutable = Join-Path $projectRoot ".venv\Scripts\python.exe"

Set-Location $projectRoot

Write-Host ""
Write-Host "AquaGuard AI - starting frontend and backend" -ForegroundColor Cyan
Write-Host "Project: $projectRoot"
Write-Host ""

if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    throw "Python virtual environment was not found. Expected: $pythonExecutable"
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker was not found. Install Docker Desktop before running AquaGuard."
}

function Test-DockerEngine {
    & docker info --format "{{.ServerVersion}}" *> $null
    return $LASTEXITCODE -eq 0
}

if (-not (Test-DockerEngine)) {
    $dockerDesktopPath = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path -LiteralPath $dockerDesktopPath)) {
        throw "Docker Desktop is installed but its application could not be found. Start Docker Desktop manually and run npm start again."
    }

    Write-Host "Docker Engine is stopped. Opening Docker Desktop..." -ForegroundColor Yellow
    Start-Process -FilePath $dockerDesktopPath
    Write-Host "Waiting for Docker Engine (this can take one or two minutes)..." -ForegroundColor DarkGray

    $dockerDeadline = (Get-Date).AddMinutes(3)
    while ((Get-Date) -lt $dockerDeadline -and -not (Test-DockerEngine)) {
        Start-Sleep -Seconds 3
    }

    if (-not (Test-DockerEngine)) {
        throw "Docker Engine did not become ready within three minutes. Check Docker Desktop, then run npm start again."
    }
    Write-Host "Docker Engine is ready." -ForegroundColor Green
}

Write-Host "[1/3] Starting MongoDB..." -ForegroundColor Yellow
& docker compose up -d mongodb
if ($LASTEXITCODE -ne 0) {
    throw "MongoDB could not be started. Check Docker Desktop."
}

if (-not $SkipFrontendBuild) {
    Write-Host "[2/3] Building the frontend..." -ForegroundColor Yellow
    Push-Location $frontendDirectory
    try {
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend build failed. Review the error shown above."
        }
    }
    finally {
        Pop-Location
    }
}
else {
    $frontendIndex = Join-Path $frontendDirectory "dist\index.html"
    if (-not (Test-Path -LiteralPath $frontendIndex)) {
        throw "No built frontend was found. Run npm start once before npm run start:fast."
    }
    Write-Host "[2/3] Using the existing frontend build." -ForegroundColor Yellow
}

Write-Host "[3/3] Starting Uvicorn..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Open AquaGuard: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Live camera:   http://127.0.0.1:8000/live" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the application." -ForegroundColor DarkGray
Write-Host ""

Set-Location $backendDirectory
& $pythonExecutable -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
exit $LASTEXITCODE
