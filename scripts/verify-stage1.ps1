$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$requiredPaths = @(
    "README.md",
    "docs/architecture.md",
    ".env.example",
    ".gitignore",
    "backend/app/api",
    "backend/app/core",
    "backend/app/db/repositories",
    "backend/app/services",
    "backend/app/vision/risk/signals",
    "backend/tests",
    "frontend/src/api",
    "frontend/src/components",
    "frontend/src/pages",
    "storage/uploads",
    "storage/processed",
    "storage/incidents"
)

$missingPaths = foreach ($relativePath in $requiredPaths) {
    $fullPath = Join-Path $projectRoot $relativePath
    if (-not (Test-Path $fullPath)) {
        $relativePath
    }
}

if ($missingPaths) {
    Write-Error "Stage 1 is incomplete. Missing: $($missingPaths -join ', ')"
}

Write-Host "Stage 1 structure is valid." -ForegroundColor Green
