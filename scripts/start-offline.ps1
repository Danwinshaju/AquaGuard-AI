$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$frontendIndex = Join-Path $projectRoot "frontend\dist\index.html"
$mongoArchive = Join-Path $projectRoot "offline\mongo-8.0.tar"

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Offline setup is not complete. Run .\scripts\setup-offline.ps1 first."
}
if (-not (Test-Path -LiteralPath $frontendIndex)) {
    throw "The compiled offline frontend is missing. Prepare the package again."
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker Desktop is not installed. Run the offline setup first."
}

function Test-DockerEngine {
    & docker info --format "{{.ServerVersion}}" *> $null
    return $LASTEXITCODE -eq 0
}

if (-not (Test-DockerEngine)) {
    $dockerDesktopPaths = @(
        (Join-Path $env:LocalAppData "Programs\DockerDesktop\Docker Desktop.exe"),
        (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe")
    )
    $dockerDesktopPath = $dockerDesktopPaths | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $dockerDesktopPath) {
        throw "Start Docker Desktop manually, wait for it to finish, then run this command again."
    }
    Start-Process -FilePath $dockerDesktopPath -WindowStyle Hidden
    Write-Host "Waiting for Docker Desktop..." -ForegroundColor Yellow
    $deadline = (Get-Date).AddMinutes(3)
    while ((Get-Date) -lt $deadline -and -not (Test-DockerEngine)) {
        Start-Sleep -Seconds 3
    }
    if (-not (Test-DockerEngine)) {
        throw "Docker Desktop did not become ready. Open it and check its message."
    }
}

& docker image inspect mongo:8.0 *> $null
if ($LASTEXITCODE -ne 0) {
    if (-not (Test-Path -LiteralPath $mongoArchive)) {
        throw "The offline MongoDB image is missing."
    }
    & docker image load --input $mongoArchive
    if ($LASTEXITCODE -ne 0) { throw "The MongoDB image could not be loaded." }
}

& docker compose --project-directory $projectRoot up -d mongodb
if ($LASTEXITCODE -ne 0) { throw "MongoDB could not be started." }

Write-Host ""
Write-Host "AquaGuard is starting without internet." -ForegroundColor Green
Write-Host "Open: http://127.0.0.1:8000"
Write-Host "Press Ctrl+C to stop AquaGuard."
Set-Location (Join-Path $projectRoot "backend")
& $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000
exit $LASTEXITCODE
