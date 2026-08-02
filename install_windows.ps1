# MediaCrush Windows installer
# Installs to the current user's app folder and creates a desktop shortcut.

$ErrorActionPreference = "Stop"

function Write-Step($Text) {
    Write-Host ""
    Write-Host $Text -ForegroundColor Cyan
}

function Resolve-Python {
    $candidates = @("py", "python")
    foreach ($candidate in $candidates) {
        try {
            if ($candidate -eq "py") {
                $version = & py -3 --version 2>&1
                if ($LASTEXITCODE -eq 0) { return @("py", "-3") }
            } else {
                $version = & python --version 2>&1
                if ($LASTEXITCODE -eq 0) { return @("python") }
            }
        } catch {
        }
    }
    throw "Python 3.8+ was not found. Install Python from https://www.python.org/downloads/ and enable 'Add Python to PATH'."
}

function Copy-AppFiles($Source, $Destination) {
    $excludeDirs = @(".git", ".venv", "__pycache__")
    $excludeFiles = @("*.pyc", "*.pyo")

    if (Test-Path $Destination) {
        Remove-Item -LiteralPath $Destination -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null

    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        if ($excludeDirs -contains $_.Name) { return }
        if ($_.Name -eq ".tools") { return }

        $target = Join-Path $Destination $_.Name
        if ($_.PSIsContainer) {
            Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse -Force -Exclude $excludeFiles
        } else {
            Copy-Item -LiteralPath $_.FullName -Destination $target -Force
        }
    }
}

function ConvertTo-VbsString($Text) {
    return $Text.Replace('"', '""')
}

$sourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$installRoot = Join-Path $env:LOCALAPPDATA "Programs\MediaCrush"
$venvDir = Join-Path $installRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$venvPythonw = Join-Path $venvDir "Scripts\pythonw.exe"
$mainPy = Join-Path $installRoot "main.py"
$launcherPath = Join-Path $installRoot "MediaCrush.vbs"

Write-Host "MediaCrush Windows installer" -ForegroundColor Magenta
Write-Host "Source:  $sourceDir"
Write-Host "Install: $installRoot"

Write-Step "[1/5] Checking Python"
$pythonCmd = Resolve-Python
Write-Host "Python found" -ForegroundColor Green

Write-Step "[2/5] Copying application files"
Copy-AppFiles -Source $sourceDir -Destination $installRoot
Write-Host "Application copied to $installRoot" -ForegroundColor Green

Write-Step "[3/5] Creating local Python environment"
if ($pythonCmd.Length -gt 1) {
    & $pythonCmd[0] $pythonCmd[1] -m venv $venvDir
} else {
    & $pythonCmd[0] -m venv $venvDir
}
if (-not (Test-Path $venvPython)) {
    throw "Failed to create virtual environment at $venvDir"
}
Write-Host "Virtual environment ready" -ForegroundColor Green

Write-Step "[4/5] Running app setup in install folder"
& $venvPython -c "import main; main.bootstrap(); print('MediaCrush setup complete')"
if ($LASTEXITCODE -ne 0) {
    throw "MediaCrush setup failed"
}

Write-Step "[5/5] Creating desktop shortcut"
$launcherPython = if (Test-Path $venvPythonw) { $venvPythonw } else { $venvPython }
$vbsInstallRoot = ConvertTo-VbsString $installRoot
$vbsPython = ConvertTo-VbsString $launcherPython
$vbsMainPy = ConvertTo-VbsString $mainPy
$launcherScript = @"
Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = "$vbsInstallRoot"
shell.Run Chr(34) & "$vbsPython" & Chr(34) & " " & Chr(34) & "$vbsMainPy" & Chr(34), 0, False
"@
Set-Content -LiteralPath $launcherPath -Value $launcherScript -Encoding ASCII

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "MediaCrush.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $env:WINDIR "System32\wscript.exe"
$shortcut.Arguments = "`"$launcherPath`""
$shortcut.WorkingDirectory = $installRoot
$shortcut.Description = "MediaCrush - Media Compression Tool"
$shortcut.Save()
Write-Host "Desktop shortcut created: $shortcutPath" -ForegroundColor Green

Write-Host ""
Write-Host "Installation complete." -ForegroundColor Green
Write-Host "Launch MediaCrush from the desktop shortcut or run:"
Write-Host "  wscript.exe `"$launcherPath`""
