param(
    [Parameter(Mandatory = $true)]
    [string]$Destination,
    [switch]$SkipInstallers
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$destinationParent = [System.IO.Path]::GetFullPath($Destination)
$packageRoot = Join-Path $destinationParent "AquaGuard-AI-Offline"

function Assert-Succeeded([string]$Step) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE."
    }
}

if (Test-Path -LiteralPath $packageRoot) {
    throw "The package folder already exists: $packageRoot. Rename or remove it yourself, then run this command again."
}

foreach ($command in @("py", "npm.cmd", "docker")) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "$command is required while preparing the offline package."
    }
}

Write-Host "AquaGuard offline-package preparation" -ForegroundColor Cyan
Write-Host "Source:      $projectRoot"
Write-Host "Destination: $packageRoot"
Write-Host "Allow at least 8 GB of free space and keep the internet connected." -ForegroundColor Yellow

Write-Host "[1/7] Building the frontend..." -ForegroundColor Yellow
Push-Location (Join-Path $projectRoot "frontend")
try {
    & npm.cmd run build
    Assert-Succeeded "Frontend build"
}
finally {
    Pop-Location
}

Write-Host "[2/7] Copying portable project files..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $packageRoot -Force | Out-Null
$excludedDirectories = @(
    (Join-Path $projectRoot ".git"),
    (Join-Path $projectRoot ".venv"),
    (Join-Path $projectRoot "frontend\node_modules"),
    (Join-Path $projectRoot "storage"),
    (Join-Path $projectRoot ".pytest_cache"),
    (Join-Path $projectRoot ".ruff_cache"),
    (Join-Path $projectRoot "backend\.pytest_cache"),
    (Join-Path $projectRoot "backend\.ruff_cache"),
    $packageRoot
)
& robocopy $projectRoot $packageRoot /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD $excludedDirectories
if ($LASTEXITCODE -ge 8) {
    throw "Project copy failed with robocopy exit code $LASTEXITCODE."
}

$offlineDirectory = Join-Path $packageRoot "offline"
$wheelDirectory = Join-Path $offlineDirectory "python-wheels"
$installerDirectory = Join-Path $offlineDirectory "installers"
New-Item -ItemType Directory -Path $wheelDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $installerDirectory -Force | Out-Null
foreach ($relativePath in @(
    "storage\uploads",
    "storage\processed",
    "storage\incidents\snapshots",
    "storage\incidents\clips",
    "storage\training"
)) {
    New-Item -ItemType Directory -Path (Join-Path $packageRoot $relativePath) -Force | Out-Null
}

Write-Host "[3/7] Downloading CPU-only PyTorch wheels..." -ForegroundColor Yellow
& py -3.11 -m pip download `
    torch==2.7.1 `
    torchvision==0.22.1 `
    --index-url https://download.pytorch.org/whl/cpu `
    --dest $wheelDirectory
Assert-Succeeded "PyTorch wheel download"

Write-Host "[4/7] Downloading all remaining Python wheels..." -ForegroundColor Yellow
& py -3.11 -m pip download `
    --requirement (Join-Path $projectRoot "backend\requirements-offline.txt") `
    --find-links $wheelDirectory `
    --dest $wheelDirectory
Assert-Succeeded "Python wheel download"

Write-Host "[5/7] Saving the MongoDB image..." -ForegroundColor Yellow
& docker pull mongo:8.0
Assert-Succeeded "MongoDB image download"
& docker image save mongo:8.0 --output (Join-Path $offlineDirectory "mongo-8.0.tar")
Assert-Succeeded "MongoDB image export"

if (-not $SkipInstallers) {
    Write-Host "[6/7] Downloading Windows installers..." -ForegroundColor Yellow
    $progressPreference = $ProgressPreference
    $ProgressPreference = "SilentlyContinue"
    try {
        Invoke-WebRequest `
            -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" `
            -OutFile (Join-Path $installerDirectory "python-3.11.9-amd64.exe")
        Invoke-WebRequest `
            -Uri "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe" `
            -OutFile (Join-Path $installerDirectory "Docker Desktop Installer.exe")
    }
    finally {
        $ProgressPreference = $progressPreference
    }
}
else {
    Write-Host "[6/7] Installer download skipped." -ForegroundColor DarkGray
}

Write-Host "[7/7] Verifying required offline files..." -ForegroundColor Yellow
$requiredFiles = @(
    (Join-Path $packageRoot "frontend\dist\index.html"),
    (Join-Path $packageRoot "backend\yolo11n.pt"),
    (Join-Path $packageRoot "backend\yolo11n-pose.pt"),
    (Join-Path $offlineDirectory "mongo-8.0.tar"),
    (Join-Path $packageRoot "scripts\setup-offline.ps1"),
    (Join-Path $packageRoot "scripts\start-offline.ps1")
)
foreach ($requiredFile in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $requiredFile)) {
        throw "Required offline file is missing: $requiredFile"
    }
}
if (-not (Get-ChildItem -LiteralPath $wheelDirectory -Filter "*.whl")) {
    throw "The Python wheelhouse is empty."
}

$sizeBytes = (Get-ChildItem -LiteralPath $packageRoot -Recurse -File | Measure-Object Length -Sum).Sum
$sizeGb = [math]::Round($sizeBytes / 1GB, 2)
Write-Host ""
Write-Host "Offline package is ready: $packageRoot" -ForegroundColor Green
Write-Host "Package size: $sizeGb GB"
Write-Host "Safely eject the pendrive. On the offline PC, open OFFLINE-README.txt." -ForegroundColor Cyan
