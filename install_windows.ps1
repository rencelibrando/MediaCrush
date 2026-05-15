# MediaCrush Windows Automatic Installation Script
# Run this script in PowerShell as Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MediaCrush Windows Installation Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator." -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit 1
}

# Check Python installation
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "✗ Python not found or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3.8 or higher from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    pause
    exit 1
}

# Check Python version
$versionOutput = python --version 2>&1
if ($versionOutput -match "Python (\d+)\.(\d+)") {
    $major = [int]$matches[1]
    $minor = [int]$matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
        Write-Host "✗ Python 3.8+ required, found $versionOutput" -ForegroundColor Red
        pause
        exit 1
    }
}

# Install Python dependencies
Write-Host ""
Write-Host "[2/5] Installing Python dependencies..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
    } else {
        throw "pip install failed"
    }
} catch {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    pause
    exit 1
}

# Check FFmpeg installation
Write-Host ""
Write-Host "[3/5] Checking FFmpeg installation..." -ForegroundColor Yellow
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ FFmpeg found: $ffmpegVersion" -ForegroundColor Green
    } else {
        throw "FFmpeg not found"
    }
} catch {
    Write-Host "✗ FFmpeg not found in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "FFmpeg is required for video compression." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Option 1: Manual Installation" -ForegroundColor Cyan
    Write-Host "  1. Download FFmpeg from: https://ffmpeg.org/download.html#build-windows" -ForegroundColor White
    Write-Host "  2. Extract the zip file" -ForegroundColor White
    Write-Host "  3. Add the bin folder to your system PATH" -ForegroundColor White
    Write-Host "  4. Restart this script" -ForegroundColor White
    Write-Host ""
    Write-Host "Option 2: Automatic Installation (recommended)" -ForegroundColor Cyan
    $installFFmpeg = Read-Host "Would you like to automatically install FFmpeg? (Y/N)"
    
    if ($installFFmpeg -eq "Y" -or $installFFmpeg -eq "y") {
        Write-Host "Downloading FFmpeg..." -ForegroundColor Yellow
        $ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        $ffmpegZip = "$env:TEMP\ffmpeg.zip"
        $ffmpegExtract = "$env:TEMP\ffmpeg_extract"
        
        try {
            # Download using Invoke-WebRequest
            Write-Host "Downloading from $ffmpegUrl..." -ForegroundColor Yellow
            Invoke-WebRequest -Uri $ffmpegUrl -OutFile $ffmpegZip -UseBasicParsing
            
            # Extract
            Write-Host "Extracting FFmpeg..." -ForegroundColor Yellow
            Expand-Archive -Path $ffmpegZip -DestinationPath $ffmpegExtract -Force
            
            # Find the extracted folder
            $extractedFolder = Get-ChildItem -Path $ffmpegExtract -Directory | Select-Object -First 1
            $binPath = Join-Path $extractedFolder.FullName "bin"
            
            # Install to Program Files
            $installPath = "C:\Program Files\FFmpeg"
            Write-Host "Installing to $installPath..." -ForegroundColor Yellow
            
            if (Test-Path $installPath) {
                Remove-Item $installPath -Recurse -Force
            }
            Copy-Item -Path $binPath -Destination $installPath -Recurse -Force
            
            # Add to PATH
            $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
            if ($currentPath -notlike "*$installPath*") {
                [Environment]::SetEnvironmentVariable("Path", "$currentPath;$installPath", "Machine")
                Write-Host "✓ FFmpeg installed and added to PATH" -ForegroundColor Green
                Write-Host "⚠ Please restart your terminal for PATH changes to take effect" -ForegroundColor Yellow
            } else {
                Write-Host "✓ FFmpeg installed (already in PATH)" -ForegroundColor Green
            }
            
            # Cleanup
            Remove-Item $ffmpegZip -Force
            Remove-Item $ffmpegExtract -Recurse -Force
            
        } catch {
            Write-Host "✗ Automatic installation failed: $_" -ForegroundColor Red
            Write-Host "Please install FFmpeg manually using Option 1 above." -ForegroundColor Yellow
            pause
            exit 1
        }
    } else {
        Write-Host "Installation cancelled. Please install FFmpeg manually." -ForegroundColor Yellow
        pause
        exit 1
    }
}

# Create desktop shortcut (optional)
Write-Host ""
Write-Host "[4/5] Creating desktop shortcut..." -ForegroundColor Yellow
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $desktop = [Environment]::GetFolderPath("Desktop")
    $shortcut = $WshShell.CreateShortcut("$desktop\MediaCrush.lnk")
    $shortcut.TargetPath = "python"
    $shortcut.Arguments = "`"$PSScriptRoot\main.py`""
    $shortcut.WorkingDirectory = $PSScriptRoot
    $shortcut.Description = "MediaCrush - Media Compression Tool"
    $shortcut.Save()
    Write-Host "✓ Desktop shortcut created" -ForegroundColor Green
} catch {
    Write-Host "⚠ Could not create desktop shortcut (not critical)" -ForegroundColor Yellow
}

# Done
Write-Host ""
Write-Host "[5/5] Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run MediaCrush by:" -ForegroundColor Cyan
Write-Host "  1. Double-click the desktop shortcut" -ForegroundColor White
Write-Host "  2. Or run: python main.py" -ForegroundColor White
Write-Host ""
Write-Host "Note: If FFmpeg was just installed, restart your terminal first." -ForegroundColor Yellow
Write-Host ""
pause
