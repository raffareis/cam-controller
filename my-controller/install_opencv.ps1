# Install OpenCV for Camera Test
Write-Host "Installing OpenCV for Camera Test..." -ForegroundColor Green

try {
    Write-Host "Installing compatible NumPy..." -ForegroundColor Yellow
    pip install "numpy<2.0.0"
    
    Write-Host "Installing opencv-python..." -ForegroundColor Yellow
    pip install opencv-python==4.8.1.78
    Write-Host "✅ OpenCV installed successfully!" -ForegroundColor Green
    
    Write-Host "`nTesting OpenCV installation..." -ForegroundColor Yellow
    python -c "import cv2; import numpy; print(f'OpenCV: {cv2.__version__}'); print(f'NumPy: {numpy.__version__}')"
    Write-Host "✅ OpenCV is working!" -ForegroundColor Green
    
    Write-Host "`n🎯 Ready to test camera!" -ForegroundColor Cyan
    Write-Host "Run: python camera_test.py" -ForegroundColor White
    
} catch {
    Write-Host "❌ Failed to install OpenCV" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "`nIf you see NumPy compatibility errors, run:" -ForegroundColor Yellow
    Write-Host "./fix_numpy_opencv.ps1" -ForegroundColor White
}

Read-Host "`nPress Enter to exit" 