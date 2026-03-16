# Schreibtafel (Digital Tablet / Chalkboard)

Schreibtafel is a digital todo application and chalkboard designed primarily for the Raspberry Pi. It features a touch-optimized UI, kiosk mode support, and handwriting recognition capabilities.

## Overview

The project consists of two main components:
- **TodoApp (`main.py`)**: A task management application with a swipeable list (swipe to complete or delete).
- **TafelApp (`tafel_main.py`)**: A digital drawing canvas (chalkboard) with a persistent storage system.

## Stack

- **Language**: Python 3 (tested on 3.11+)
- **GUI Framework**: PyQt5
- **Image Processing / OCR**: 
  - `opencv-python-headless`
  - `easyocr`
  - `pytesseract`
  - `numpy`
- **Window Management (RPi)**: `matchbox-window-manager`
- **Logging**: Syslog (`/dev/log`) and stdout via a custom logging utility.

## Requirements

The application requires Python 3.11+ and several system-level dependencies when running on a Raspberry Pi.

- **System Packages (RPi)**:
  - `python3-pyqt5` (Recommended to install via `apt` as pip compilation often fails on ARM)
  - `wlopm` (For Wayland display power management)
  - `matchbox-window-manager` (For fullscreen kiosk mode)
  - `xset` (For X11 DPMS settings)

- **Python Dependencies**:
  - Listed in `requirements.txt`.

## Setup & Run

### 1. Installation

On a Raspberry Pi (PiOS), it's recommended to install PyQt5 via the package manager first:
```bash
sudo apt update
sudo apt install -y python3-pyqt5
```

Install other Python dependencies:
```bash
pip install -r requirements.txt
```

### 2. Running in Kiosk Mode (Raspberry Pi)

Use the provided `start_tafel.sh` script to launch the application in a dedicated kiosk environment. This script handles:
- Updating the code via `git pull`.
- Setting up a virtual environment (`.venv`) with access to system site packages.
- Configuring Wayland and X11 environment variables.
- Waking up the display.
- Starting the `matchbox-window-manager`.
- Launching `main.py`.

```bash
chmod +x start_tafel.sh
./start_tafel.sh
```

### 3. Running Locally (Development)

You can run the applications directly using Python:
```bash
python main.py        # Starts the Todo Application
python tafel_main.py  # Starts the Drawing/Chalkboard Application
```

## Scripts

- **`start_tafel.sh`**: The main entry point for the Raspberry Pi kiosk system.
- **`wake_display.sh`**: A utility script to manually wake up the display using `wlopm` (Wayland) and `xset` (X11).

## Environment Variables

The following environment variables are used, particularly in the kiosk mode:
- `WAYLAND_DISPLAY`: Set to `wayland-0` for display management.
- `XDG_RUNTIME_DIR`: Runtime directory for user processes.
- `DISPLAY`: Set to `:0` for X11 applications.
- `QT_QPA_PLATFORM`: Set to `xcb` for Qt's platform plugin.
- `QT_IM_MODULE`: Set to `qtvirtualkeyboard` to enable the on-screen keyboard.

## Project Structure

- `main.py`: Entry point for the Todo application.
- `tafel_main.py`: Entry point for the digital chalkboard application.
- `task_manager.py`: Handles task persistence (JSON) and logic.
- `hwr_manager.py`: Manages handwriting recognition logic.
- `drawing_widget.py`: Custom widget for drawing/writing.
- `modules/config.py`: Singleton configuration management.
- `modules/Mhandle_log.py`: Centralized logging utility.
- `style.py`: QSS stylesheet for the UI.
- `requirements.txt`: Python package requirements.

## Configuration

Settings such as `WAKE_HOUR` and `SLEEP_HOUR` (24h format) can be modified in `modules/config.py`. The application automatically manages display power states based on these hours.

## Testing

Currently, logic tests use the built-in `unittest` module.

### Running Tests
```bash
python -m unittest discover
```

### Adding New Tests
- Logic tests should inherit from `unittest.TestCase`.
- For GUI-specific testing, use `pytest-qt`.

**TODO**: Add a comprehensive test suite to the repository.

## License

**TODO**: Specify license (e.g., MIT, GPL).
