# Para Controller POC - Virtual Joystick Test

This is a proof of concept for a virtual paragliding controller that emulates the Para Controller Mini using vJoy.

## Features

- **Virtual Controller**: Creates a virtual joystick that Windows recognizes
- **GUI Interface**: Sliders and buttons to test controller functionality
- **Para Controller Mapping**: Matches the exact axis ranges and button count of Para Controller Mini
- **Real-time Updates**: Controller state updates instantly as you move sliders

## Controller Mapping

Based on the Para Controller Mini specifications:

- **X-Axis**: Left brake control (-127 to 127)
- **Y-Axis**: Right brake control (-127 to 127)
- **Z-Axis**: Speed bar control (-127 to 127)
- **X-Rotation**: Weight shift control (0 to 359 degrees)
- **4 Buttons**: For various functions

## Requirements

### Software

1. **vJoy Driver**: Download and install from [vJoy official website](http://vjoystick.sourceforge.net/site/)
2. **Python 3.7+**: With pip installed
3. **Python packages**: Install via `pip install -r requirements.txt`

### vJoy Configuration

1. Install vJoy driver
2. Open vJoy Config (Start Menu > vJoy > Configure vJoy)
3. Select Device 1 and configure:
   - **Axes**: X, Y, Z, Rx (4 axes minimum)
   - **Buttons**: 4 minimum
   - Click "Apply" to save configuration

## Installation

1. Clone or download this repository
2. Install vJoy driver (see requirements above)
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Make sure vJoy is installed and configured
2. Run the proof of concept:
   ```bash
   python controller_poc.py
   ```
3. The GUI window will open with sliders for each axis and checkboxes for buttons
4. Move sliders and click buttons to test the virtual controller

## Testing with Games

1. **Verify Controller Detection**:

   - Click "Open Game Controllers" button in the app
   - OR manually open: Control Panel > Hardware and Sound > Game Controllers
   - You should see "vJoy Device" listed

2. **Test in GliderSim**:
   - Launch GliderSim
   - Go to controller settings
   - Select "Para Controller" or the vJoy device
   - Move the sliders in the POC app to test if GliderSim responds

## Troubleshooting

### "Failed to initialize vJoy device"

- Make sure vJoy driver is installed
- Check vJoy configuration (Device 1 should be enabled)
- Restart the application
- Try running as Administrator

### Controller not detected in games

- Verify in Windows Game Controllers panel
- Restart the game after starting the POC app
- Check game controller settings

### Sliders not responding

- Check console for error messages
- Verify vJoy device is properly configured
- Try different axis mappings in game settings

## Next Steps

This POC validates that:

1. ✅ Virtual controller can be created and recognized by Windows
2. ✅ Controller axes and buttons work correctly
3. ✅ Real-time updates function properly

Once verified with GliderSim, we can proceed to implement:

- Camera input and computer vision
- Hand tracking and gesture recognition
- Blue glove detection
- Automatic calibration

## Camera Test

A new camera test module has been added:

### Quick Camera Test

```bash
# Install OpenCV
./install_opencv.ps1

# If you get NumPy compatibility errors, run:
./fix_numpy_opencv.ps1

# Test camera
python camera_test.py
```

### Features

- **Multiple Camera Sources**: Tests built-in webcam and IP Webcam from phone
- **Real-time Preview**: Shows live camera feed with FPS counter
- **Easy Switching**: Press 'c' to cycle through available cameras
- **Phone Camera Support**: Works with IP Webcam app on Android/iPhone

### Camera Setup for Phone

1. **Android**: Install "IP Webcam" app
2. **iPhone**: Install "EpocCam" or similar
3. Start the app and note the IP address (e.g., 192.168.1.100:8080)
4. Update the IP addresses in `camera_test.py` if needed
5. Make sure phone and computer are on same WiFi

## Blue Glove Controller - READY TO TEST! 🎮

The main blue glove controller is now ready:

### Quick Start

```bash
# Put on blue gloves or hold blue objects
python blue_glove_controller.py
```

### Features

- **Real-time blue object detection** (gloves, clothes, any blue items)
- **Hand position tracking** (left/right hand separation)
- **Virtual controller output** (works with GliderSim!)
- **Live preview** with detection overlay
- **Smooth controls** with jitter reduction

### Control Mapping

- **Left hand position** → **Left brake** (X-axis)
- **Right hand position** → **Right brake** (Y-axis)
- **Vertical hand position** → **Speed bar** (Z-axis)
- **Center of both hands** → **Weight shift** (X-rotation)

### Controls

- `q` or `ESC`: Quit
- `c`: Switch camera source
- `r`: Reset controller to neutral
- `s`: Save current frame
- `h`: Show help

### Testing with GliderSim

1. Start the blue glove controller first
2. Launch GliderSim
3. Configure controller to use "vJoy Device"
4. Put on blue gloves and fly! ✈️

## Hand Tracking Controller - NO GLOVES NEEDED! 👋

The newest and most advanced controller uses MediaPipe hand tracking:

### Quick Start

```bash
# Install MediaPipe
./install_mediapipe.ps1

# Test hand detection first
python test_hand_detection.py

# Run the full controller
python hand_tracking_controller.py
```

### Features

- **No equipment needed** - just use your bare hands!
- **Advanced hand tracking** with MediaPipe AI
- **Gesture recognition** (fist, point, peace, thumbs up)
- **Left/right hand distinction**
- **Real-time 21-point hand landmarks**
- **Mirror mode** for intuitive control
- **Smooth and responsive** with built-in filtering

### Hand Controls

- **Left hand position** → **Left brake**
- **Right hand position** → **Right brake**
- **Vertical position** → **Speed bar** (up = pull, down = push)
- **Center of hands** → **Weight shift**

### Gesture Controls (Toggle with 'g')

- **Fist** → Button 1
- **Point** (index finger) → Button 2
- **Peace** (V sign) → Button 3
- **Thumbs up** → Button 4

### Controls

- `q` or `ESC`: Quit
- `r`: Reset controller to neutral
- `g`: Toggle gesture detection
- `s`: Save current frame
- `h`: Show help

### Why Hand Tracking is Better

- ✅ **No special equipment** - works with any hands
- ✅ **Works in any lighting** - no color detection issues
- ✅ **More precise** - 21 landmark points per hand
- ✅ **Gesture support** - buttons via hand gestures
- ✅ **More natural** - intuitive hand movements

## Files

### Main Applications

- `hand_tracking_controller.py`: **🌟 BEST** - AI hand tracking (no equipment needed!)
- `pink_glove_controller.py`: Pink object detection → virtual controller
- `controller_poc.py`: Virtual controller test with GUI sliders

### Testing & Setup

- `test_hand_detection.py`: Test MediaPipe hand tracking
- `test_pink_detection.py`: Test pink object detection
- `camera_test.py`: Camera capture test with OpenCV
- `setup_check.py`: Verify all dependencies are installed

### Installation Scripts

- `install_mediapipe.ps1`: Install MediaPipe for hand tracking
- `install_opencv.ps1`: Install OpenCV for camera test
- `install_dependencies.ps1`: Install basic dependencies
- `fix_numpy_opencv.ps1`: Fix NumPy/OpenCV compatibility issues

### Configuration

- `requirements.txt`: Python dependencies
- `README.md`: This documentation
