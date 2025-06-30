# MediaPipe Manual Installation Guide

If the automatic installation failed, try these manual steps:

## Option 1: Basic Installation

```bash
pip install mediapipe
```

## Option 2: User Installation

```bash
pip install --user mediapipe
```

## Option 3: Force Upgrade

```bash
pip install --upgrade --force-reinstall mediapipe
```

## Option 4: Specific Python Command

```bash
python -m pip install mediapipe
```

## Option 5: Update pip first

```bash
pip install --upgrade pip
pip install mediapipe
```

## Check Your Python Version

MediaPipe requires Python 3.7-3.11. Check your version:

```bash
python --version
```

## Test Installation

After installation, test if it works:

```bash
python -c "import mediapipe as mp; print('MediaPipe version:', mp.__version__); print('✅ Working!')"
```

## If Nothing Works

You can still use the other controllers:

- `python controller_poc.py` - GUI with sliders (always works)
- `python pink_glove_controller.py` - Color detection (needs OpenCV only)

## Alternative: Use Pink Glove Controller

The pink glove controller is simpler and more reliable:

1. Get any pink object (gloves, clothing, toy, etc.)
2. Run: `python pink_glove_controller.py`
3. Hold the pink object and move your hands!

## Common Issues

- **Python too old/new**: MediaPipe needs Python 3.7-3.11
- **Missing Visual C++**: Install Microsoft Visual C++ Redistributable
- **Firewall/Antivirus**: May block pip downloads
- **Corporate network**: May need proxy settings
