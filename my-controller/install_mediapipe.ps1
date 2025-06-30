# Install MediaPipe for Hand Tracking Controller
Write-Host "Installing MediaPipe for Hand Tracking..." -ForegroundColor Green

try {
    Write-Host "Installing MediaPipe..." -ForegroundColor Yellow
    Write-Host "Trying latest compatible version..." -ForegroundColor Cyan
    
    # Try different installation methods
    $success = $false
    
    # Method 1: Latest version
    try {
        pip install mediapipe
        $success = $true
        Write-Host "✅ MediaPipe installed successfully (latest version)!" -ForegroundColor Green
    } catch {
        Write-Host "Method 1 failed, trying specific version..." -ForegroundColor Yellow
    }
    
    # Method 2: Try a known stable version
    if (-not $success) {
        try {
            pip install mediapipe==0.10.8
            $success = $true
            Write-Host "✅ MediaPipe installed successfully (v0.10.8)!" -ForegroundColor Green
        } catch {
            Write-Host "Method 2 failed, trying older version..." -ForegroundColor Yellow
        }
    }
    
    # Method 3: Try older but stable version
    if (-not $success) {
        try {
            pip install mediapipe==0.10.3
            $success = $true
            Write-Host "✅ MediaPipe installed successfully (v0.10.3)!" -ForegroundColor Green
        } catch {
            Write-Host "Method 3 failed, trying basic installation..." -ForegroundColor Yellow
        }
    }
    
    # Method 4: Force reinstall
    if (-not $success) {
        pip install --upgrade --force-reinstall mediapipe
        $success = $true
        Write-Host "✅ MediaPipe installed successfully (force reinstall)!" -ForegroundColor Green
    }
    
    Write-Host "`nTesting MediaPipe installation..." -ForegroundColor Yellow
    python -c "import mediapipe as mp; import cv2; print(f'MediaPipe: {mp.__version__}'); print('✅ MediaPipe is working!')"
    Write-Host "✅ MediaPipe is working!" -ForegroundColor Green
    
    Write-Host "`n🎯 Ready to test hand tracking!" -ForegroundColor Cyan
    Write-Host "Run: python test_hand_detection.py" -ForegroundColor White
    Write-Host "Or: python hand_tracking_controller.py" -ForegroundColor White
    
} catch {
    Write-Host "❌ Failed to install MediaPipe" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "`n💡 Alternative solutions:" -ForegroundColor Yellow
    Write-Host "1. Try: pip install --upgrade pip" -ForegroundColor White
    Write-Host "2. Try: pip install mediapipe --user" -ForegroundColor White
    Write-Host "3. Try: python -m pip install mediapipe" -ForegroundColor White
    Write-Host "4. Check Python version: python --version" -ForegroundColor White
    Write-Host "   (MediaPipe needs Python 3.7-3.11)" -ForegroundColor White
    $success = $false
}

if (-not $success) {
    Write-Host "`n⚠️  MediaPipe installation failed!" -ForegroundColor Red
    Write-Host "You can still use the other controllers:" -ForegroundColor Yellow
    Write-Host "- python controller_poc.py (sliders)" -ForegroundColor White
    Write-Host "- python pink_glove_controller.py (color detection)" -ForegroundColor White
}

Read-Host "`nPress Enter to exit" 