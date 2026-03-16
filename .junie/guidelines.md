# Project Guidelines

This document provides essential information for developers working on the Schreibtafel project.

### 1. Build/Configuration Instructions

- **Environment**: Python 3.x (tested on 3.11+).
- **GUI Framework**: PyQt5.
- **Target Platform**: Raspberry Pi (PiOS), although it can run on other systems for development.
- **Setup**:
  1. Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
  2. **Kiosk Mode (Raspberry Pi)**: Use `start_tafel.sh` to launch. This script:
     - Pulls the latest changes from Git.
     - Configures Wayland/X11 environment variables.
     - Wakes up the screen using `wlopm` and `xset`.
     - Starts `matchbox-window-manager` to handle the fullscreen layout without title bars.
- **Config**: Settings like `WAKE_HOUR` and `SLEEP_HOUR` are managed in `modules/config.py`.

### 2. Testing Information

- **Framework**: Use the built-in `unittest` module for logic tests.
- **Execution**:
  - Run all tests: `python -m unittest discover`
  - Run a specific test: `python test_task_manager.py`
- **Adding New Tests**:
  - Logic tests (non-GUI) should inherit from `unittest.TestCase`.
  - For GUI-specific testing, it is recommended to install and use `pytest-qt`.
- **Verified Demo Test**:
  ```python
  import unittest
  import os
  from task_manager import TaskManager

  class TestTaskManager(unittest.TestCase):
      def setUp(self):
          self.test_file = "temp_test.json"
          self.manager = TaskManager(self.test_file)
      def tearDown(self):
          if os.path.exists(self.test_file): os.remove(self.test_file)
      def test_save_and_load(self):
          tasks = [["Task 1", False], ["Task 2", True]]
          self.manager.save_tasks(tasks)
          self.assertEqual(self.manager.load_tasks(), tasks)

  if __name__ == "__main__":
      unittest.main()
  ```

### 3. Additional Development Information

- **Architecture**:
  - `main.py`: Entry point and UI logic (`TodoApp`).
  - `task_manager.py`: Business logic for task persistence (JSON format).
  - `modules/config.py`: Centralized configuration (Singleton) and logger access.
  - `modules/Mhandle_log.py`: Logging utility supporting both stdout and Syslog (`/dev/log`).
  - `style.py`: UI styling via QSS.
- **Code Style**: Follow PEP 8 conventions.
- **Logging**:
  - Access the logger via `Config().get_logger()`.
  - On Raspberry Pi, logs are typically sent to `/dev/log`.
- **UI Customization**: `SwipeListWidget` in `main.py` implements custom mouse events for touch interaction (swipe-to-complete/delete behavior).
