# Para Controller POC - Dependency Installation Script
# This script helps install Python dependencies and provides vJoy installation guidance

Write-Host "Para Controller POC - Dependency Installation" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Check if Python is installed
Write-Host "`nChecking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>$null
    if ($pythonVersion) {
        Write-Host "Python found: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "ERROR: Python not found. Please install Python 3.7+ from https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if pip is available
Write-Host "`nChecking pip..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version 2>$null
    if ($pipVersion) {
        Write-Host "pip found: $pipVersion" -ForegroundColor Green
    } else {
        throw "pip not found"
    }
} catch {
    Write-Host "ERROR: pip not found. Please reinstall Python with pip included." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install Python packages
Write-Host "`nInstalling Python packages..." -ForegroundColor Yellow
try {
    Write-Host "Installing pyvjoy..."
    pip install pyvjoy==1.0.1
    Write-Host "Installing numpy..."
    pip install numpy==1.24.3
    Write-Host "Python packages installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install Python packages. Check your internet connection and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# vJoy installation guidance
Write-Host "`n================================================" -ForegroundColor Green
Write-Host "vJoy Driver Installation Required" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Green

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Download vJoy driver from: http://vjoystick.sourceforge.net/site/" -ForegroundColor White
Write-Host "2. Install the vJoy driver (may require restart)" -ForegroundColor White
Write-Host "3. Open 'vJoy Configuration' from Start Menu" -ForegroundColor White
Write-Host "4. Configure Device 1 with:" -ForegroundColor White
Write-Host "   - Axes: X, Y, Z, Rx with 4 axes minimum" -ForegroundColor White
Write-Host "   - Buttons: 4 minimum" -ForegroundColor White
Write-Host "   - Click 'Apply' to save" -ForegroundColor White
Write-Host "5. Run setup check: python setup_check.py" -ForegroundColor White
Write-Host "6. Run the POC: python controller_poc.py" -ForegroundColor White

# Offer to open vJoy download page
Write-Host "`nWould you like to open the vJoy download page now? (y/n): " -ForegroundColor Cyan -NoNewline
$response = Read-Host
if ($response -eq 'y' -or $response -eq 'Y') {
    Start-Process "http://vjoystick.sourceforge.net"
    Write-Host "Opening vJoy download page in your browser..." -ForegroundColor Green
}

Write-Host "`nPython dependencies installed successfully!" -ForegroundColor Green
Write-Host "Do not forget to install and configure vJoy driver before running the POC." -ForegroundColor Yellow

Read-Host "`nPress Enter to exit" 