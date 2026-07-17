param(
    [string]$Dataset = "C:\Users\ELCOT\Downloads\Swimming and Drowning Detection.v1i.yolov12",
    [ValidateRange(1, 500)]
    [int]$Epochs = 50,
    [ValidateRange(1, 128)]
    [int]$Batch = 8,
    [ValidateRange(0.01, 1.0)]
    [double]$Fraction = 1.0,
    [string]$Device = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$backendDirectory = Join-Path $projectRoot "backend"
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python environment is missing: $python"
}
if (-not (Test-Path -LiteralPath $Dataset)) {
    throw "Dataset folder is missing: $Dataset"
}

Write-Host "AquaGuard aquatic YOLO training" -ForegroundColor Cyan
Write-Host "Dataset: $Dataset"
Write-Host "Epochs:  $Epochs"
Write-Host "Batch:   $Batch"
Write-Host "Data:    $([math]::Round($Fraction * 100, 0))%"
Write-Host "Device:  $(if ($Device) { $Device } else { 'automatic' })"
Write-Host "This can take many hours on CPU. Keep the terminal and computer running." -ForegroundColor Yellow

Set-Location $backendDirectory
$arguments = @(
    "-m", "ml.train_aquatic_detector",
    $Dataset,
    "--epochs", $Epochs,
    "--batch", $Batch,
    "--fraction", $Fraction.ToString([System.Globalization.CultureInfo]::InvariantCulture)
)
if ($Device) {
    $arguments += @("--device", $Device)
}
& $python @arguments
exit $LASTEXITCODE
