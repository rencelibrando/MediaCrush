# MediaCrush Windows Auto-Updater
# Automatically syncs local changes or pulls latest updates into %LOCALAPPDATA%\Programs\MediaCrush

$ErrorActionPreference = "Stop"

function Write-Step($Text) {
    Write-Host ""
    Write-Host $Text -ForegroundColor Cyan
}

function Write-Success($Text) {
    Write-Host $Text -ForegroundColor Green
}

$sourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$installRoot = Join-Path $env:LOCALAPPDATA "Programs\MediaCrush"
$venvDir = Join-Path $installRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

Write-Host "MediaCrush Windows Auto-Updater" -ForegroundColor Magenta
Write-Host "Source:  $sourceDir"
Write-Host "Target:  $installRoot"

if (-not (Test-Path $installRoot)) {
    Write-Host "MediaCrush is not installed yet. Running install_windows.ps1..."
    & (Join-Path $sourceDir "install_windows.ps1")
    exit $LASTEXITCODE
}

Write-Step "[1/4] Updating application files"
$excludeDirs = @(".git", ".venv", "__pycache__", ".tools")
$excludeFiles = @("*.pyc", "*.pyo")

Get-ChildItem -LiteralPath $sourceDir -Force | ForEach-Object {
    if ($excludeDirs -contains $_.Name) { return }
    $target = Join-Path $installRoot $_.Name
    if ($_.PSIsContainer) {
        Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse -Force -Exclude $excludeFiles
    } else {
        Copy-Item -LiteralPath $_.FullName -Destination $target -Force
    }
}
Write-Success "Files updated successfully."

Write-Step "[2/4] Updating Python dependencies"
if (Test-Path $venvPython) {
    & $venvPython -m pip install --upgrade pip setuptools wheel --quiet
    $reqFile = Join-Path $installRoot "requirements.txt"
    if (Test-Path $reqFile) {
        & $venvPython -m pip install -r $reqFile --quiet
    }
    Write-Success "Dependencies updated."
}

Write-Step "[3/4] Verifying setup"
& $venvPython -c "import main; main.bootstrap(); print('Installed version verification: OK')"

Write-Host ""
Write-Success "MediaCrush was successfully updated!"
