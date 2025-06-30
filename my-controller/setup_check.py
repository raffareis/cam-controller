"""
Setup Check Script for Para Controller POC

This script checks if all requirements are properly installed and configured.
"""

import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Need Python 3.7+")
        return False

def check_package(package_name):
    """Check if a Python package is installed"""
    spec = importlib.util.find_spec(package_name)
    if spec is not None:
        print(f"✅ {package_name} - Installed")
        return True
    else:
        print(f"❌ {package_name} - Not installed")
        return False

def check_vjoy():
    """Check if vJoy is installed and configured"""
    print("\nChecking vJoy installation...")
    
    try:
        import pyvjoy
        
        # Try to create a vJoy device
        try:
            device = pyvjoy.VJoyDevice(1)
            print("✅ vJoy Device 1 - Available")
            
            # Check if device has required axes
            print("Checking vJoy configuration...")
            
            # Test setting axes (this will fail if axes are not configured)
            try:
                device.set_axis(pyvjoy.HID_USAGE_X, 16384)
                device.set_axis(pyvjoy.HID_USAGE_Y, 16384)
                device.set_axis(pyvjoy.HID_USAGE_Z, 16384)
                device.set_axis(pyvjoy.HID_USAGE_RX, 16384)
                print("✅ Required axes (X, Y, Z, RX) - Configured")
                
                # Test buttons
                device.set_button(1, True)
                device.set_button(1, False)
                print("✅ Buttons - Working")
                
                return True
                
            except Exception as e:
                print(f"❌ vJoy configuration error: {e}")
                print("Please configure vJoy Device 1 with X, Y, Z, RX axes and at least 4 buttons")
                return False
                
        except Exception as e:
            print(f"❌ vJoy Device 1 not available: {e}")
            print("Please install and configure vJoy driver")
            return False
            
    except ImportError:
        print("❌ pyvjoy package not installed")
        return False

def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        print("✅ tkinter - Available")
        return True
    except ImportError:
        print("❌ tkinter - Not available (usually comes with Python)")
        return False

def main():
    print("Para Controller POC - Setup Check")
    print("=" * 40)
    
    all_good = True
    
    # Check Python version
    if not check_python_version():
        all_good = False
    
    print("\nChecking Python packages...")
    
    # Check required packages
    required_packages = ['pyvjoy', 'numpy', 'cv2', 'mediapipe']
    for package in required_packages:
        if not check_package(package):
            all_good = False
    
    # Check tkinter (built-in)
    if not check_tkinter():
        all_good = False
    
    # Check vJoy
    if not check_vjoy():
        all_good = False
    
    print("\n" + "=" * 40)
    
    if all_good:
        print("🎉 All checks passed! You're ready to run the POC.")
        print("\nTo start the application, run:")
        print("python controller_poc.py")
    else:
        print("❌ Some requirements are missing. Please address the issues above.")
        print("\nInstallation steps:")
        print("1. Install vJoy driver from: http://vjoystick.sourceforge.net/site/")
        print("2. Configure vJoy Device 1 with X, Y, Z, RX axes and 4+ buttons")
        print("3. Install Python packages: pip install -r requirements.txt")
    
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main() 