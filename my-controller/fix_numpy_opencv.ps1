# Fix NumPy/OpenCV Compatibility Issue
Write-Host "Fixing NumPy/OpenCV Compatibility Issue..." -ForegroundColor Green

Write-Host "`nThe issue: OpenCV was compiled for NumPy 1.x but you have NumPy 2.x installed" -ForegroundColor Yellow
Write-Host "Solution: Downgrade NumPy to compatible version" -ForegroundColor Yellow

try {
    Write-Host "`n1. Uninstalling current NumPy..." -ForegroundColor Cyan
    pip uninstall numpy -y
    
    Write-Host "`n2. Uninstalling current OpenCV..." -ForegroundColor Cyan  
    pip uninstall opencv-python -y
    
    Write-Host "`n3. Installing compatible NumPy (1.x)..." -ForegroundColor Cyan
    pip install "numpy<2.0.0"
    
    Write-Host "`n4. Installing OpenCV..." -ForegroundColor Cyan
    pip install opencv-python==4.8.1.78
    
    Write-Host "`n5. Testing the fix..." -ForegroundColor Cyan
    python -c "import cv2; import numpy; print(f'✅ OpenCV: {cv2.__version__}'); print(f'✅ NumPy: {numpy.__version__}')"
    
    Write-Host "`n🎉 Fix completed successfully!" -ForegroundColor Green
    Write-Host "You can now run: python camera_test.py" -ForegroundColor White
    
} catch {
    Write-Host "`n❌ Error during fix:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "`nTry running as Administrator or manually:" -ForegroundColor Yellow
    Write-Host "pip uninstall numpy opencv-python -y" -ForegroundColor White
    Write-Host "pip install numpy<2.0.0 opencv-python==4.8.1.78" -ForegroundColor White
}

Read-Host "`nPress Enter to exit" 