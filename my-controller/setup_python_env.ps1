# Setup Python Environment for MediaPipe
# This script helps create a virtual environment with Python 3.11

Write-Host "Python Environment Setup for MediaPipe" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

# Check current Python version
Write-Host "`nChecking current Python version..." -ForegroundColor Yellow
$currentPython = python --version 2>&1
Write-Host "Current Python: $currentPython" -ForegroundColor Cyan

# Check if we have Python 3.11 available
Write-Host "`nChecking for Python 3.11..." -ForegroundColor Yellow

$python311Found = $false
$python311Path = ""

# Common locations for Python 3.11
$possiblePaths = @(
    "py -3.11",
    "python3.11",
    "C:\Python311\python.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\python.exe"
)

foreach ($path in $possiblePaths) {
    try {
        if ($path -eq "py -3.11") {
            $version = & py -3.11 --version 2>&1
        } else {
            $version = & $path --version 2>&1
        }
        
        if ($version -match "Python 3\.11") {
            Write-Host "✅ Found Python 3.11: $path" -ForegroundColor Green
            $python311Found = $true
            $python311Path = $path
            break
        }
    } catch {
        # Silently continue if command not found
    }
}

if (-not $python311Found) {
    Write-Host "❌ Python 3.11 not found!" -ForegroundColor Red
    Write-Host "`n💡 Solutions:" -ForegroundColor Yellow
    Write-Host "1. Install Python 3.11 from python.org" -ForegroundColor White
    Write-Host "2. Use conda/miniconda (recommended)" -ForegroundColor White
    Write-Host "3. Use pyenv-win for version management" -ForegroundColor White
    Write-Host "`nSee install_python311.md for detailed instructions" -ForegroundColor Cyan
    Read-Host "`nPress Enter to exit"
    exit 1
}

# Create virtual environment
Write-Host "`nCreating virtual environment with Python 3.11..." -ForegroundColor Yellow

$envName = "paraglider-env"
$envPath = ".\$envName"

try {
    if ($python311Path -eq "py -3.11") {
        & py -3.11 -m venv $envName
    } else {
        & $python311Path -m venv $envName
    }
    
    Write-Host "✅ Virtual environment created: $envName" -ForegroundColor Green
    
    # Activate the environment
    Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
    & "$envPath\Scripts\Activate.ps1"
    
    # Check Python version in the new environment
    $newVersion = python --version
    Write-Host "✅ Environment Python version: $newVersion" -ForegroundColor Green
    
    # Install packages
    Write-Host "`nInstalling required packages..." -ForegroundColor Yellow
    
    # Upgrade pip first
    python -m pip install --upgrade pip
    
    # Install packages one by one with progress
    $packages = @("pyvjoy", "numpy<2.0.0", "opencv-python", "mediapipe")
    
    foreach ($package in $packages) {
        Write-Host "Installing $package..." -ForegroundColor Cyan
        pip install $package
    }
    
    Write-Host "`n🎉 Environment setup complete!" -ForegroundColor Green
    Write-Host "`nTo use this environment:" -ForegroundColor Yellow
    Write-Host "1. Activate: .\$envName\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "2. Run apps: python hand_tracking_controller.py" -ForegroundColor White
    Write-Host "3. Deactivate: deactivate" -ForegroundColor White
    
    # Test MediaPipe installation
    Write-Host "`nTesting MediaPipe..." -ForegroundColor Yellow
    python -c "import mediapipe as mp; print('✅ MediaPipe version:', mp.__version__)"
    
    Write-Host "`n✨ Ready to use hand tracking!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}

Read-Host "`nPress Enter to exit" 