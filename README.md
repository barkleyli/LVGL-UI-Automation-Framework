# LVGL UI Automation Framework

[![Build Status](https://github.com/barkleyli/LVGL-UI-Automation-Framework/actions/workflows/ci.yml/badge.svg)](https://github.com/barkleyli/LVGL-UI-Automation-Framework/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![LVGL](https://img.shields.io/badge/LVGL-9.x-blue.svg)](https://lvgl.io/)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)

A comprehensive testing and automation framework for LVGL-based user interfaces. Enables automated UI testing, screenshot capture, and interaction simulation for embedded and desktop applications including smartwatch interfaces with swipe gesture support.

## Features

- **Real-time UI Automation**: Click, longpress, and swipe gesture simulation
- **Screenshot Capture**: High-quality PNG screenshots for visual validation
- **Swipe Gesture Support**: Smooth panning with real-time visual feedback
- **Cross-platform Support**: Windows, Linux, and macOS compatibility
- **Python Test Framework**: Object-oriented testing with pytest integration (Tested on Windows 11)
- **Network Interface**: JSON-based TCP communication protocol
- **Widget Management**: ID-based widget registry enabled testibilty for reliable test scripts
- **Test Isolation**: Automatic UI state reset between test runs

## Quick Start

### Prerequisites

- **CMake** 3.16 or higher
- **LVGL** 9.x development libraries
- **SDL2** development libraries
- **Python** 3.8+ with pip
- **Git** for cloning the repository

### Installation

#### 1. Clone the Repository
```bash
git clone --recursive https://github.com/barkleyli/LVGL-UI-Automation-Framework.git
cd lvgl-ui-automation
```

**Note**: This repository uses Git submodules for LVGL and LodePNG dependencies. The `--recursive` flag automatically initializes and clones the submodules. SDL2 development libraries are included for Windows support.

If you forgot the `--recursive` flag, run:
```bash
git submodule update --init --recursive
```

#### 2. Build the Framework
```bash
# Windows (with Visual Studio)
./build.bat

# Linux/macOS  
./build.sh
```

#### 3. Install Python Client
```bash
cd python-client
pip install -e .
```

#### 4. Run Demo
```bash
# Start the automation server
./build/Release/lvgl-ui-automation.exe

# In another terminal, run the comprehensive demo
cd python-client
python demo.py
```

## Usage

### Basic UI Automation

```python
from lvgl_client import LVGLTestClient

# Connect to the automation server
with LVGLTestClient() as client:
    # Take initial screenshot
    client.screenshot('screenshots/initial.png')
    
    # Interact with UI elements
    client.click('btn_heart')
    client.wait(1000)  # Wait 1 second
    
    # Capture result
    client.screenshot('screenshots/after_click.png')
    
    ```

### Test Suite Integration

```python
import pytest
from lvgl_client import LVGLTestClient

class TestSmartWatch:
    @pytest.fixture
    def client(self):
        with LVGLTestClient() as client:
            yield client
    
    def test_heart_rate_measurement(self, client):
        # Initial state verification
        initial_text = client.get_state('lbl_bpm')
        assert 'BPM' in initial_text
        
        # Navigate to heart rate screen
        client.click('btn_heart')
        client.wait(500)
        
        # Start measurement with longpress
        client.longpress('hr_measure_area', 2000)
        client.wait(500)
        
        # Verify measurement started
        client.screenshot('screenshots/measuring.png')
        measuring_text = client.get_state('lbl_hr_instruction')
        assert 'measuring' in measuring_text.lower()
        
        # Wait for completion and verify result
        client.wait(3500)  # Wait for measurement cycle
        final_value = client.get_state('lbl_hr_value')
        assert 'BPM' in final_value
```

## Architecture

### System Overview

```
+-------------------+    TCP/JSON     +--------------------+
|   Python Test     |<--------------->|   C++ Server       |
|     Client        |    Port 12345   |   (LVGL + SDL2)    |
+-------------------+                 +--------------------+
        |                                     |
        v                                     v
+-------------------+                 +--------------------+
|     pytest       |                 |  UI Application    |
|   Test Suite     |                 | (Smartwatch Face)  |
+-------------------+                 +--------------------+
```

### Core Components

- **src/main.c**: LVGL application host with SDL2 backend and gesture support
- **src/test_harness.c**: Widget interaction and state management  
- **src/screenshot.c**: Real-time UI capture and PNG generation
- **src/tcp_server.c**: Network communication and command processing
- **src/ui_watch.c**: Smartwatch UI implementation with swipe gestures
- **python-client/**: High-level automation and testing framework

### Key Features

**Click, Longpress, Swipe Gesture System**
- Support click, Longpress, and swipe operations
- Support for horizontal swipe navigation between watch screens
- Real-time panning with visual feedback during drag operations
- Configurable swipe thresholds and snap behavior

**Test Isolation**
- Automatic UI state reset between test runs
- Multiple fallback methods for returning to main screen
- Robust error handling and recovery mechanisms
- Prevents test hanging on consecutive runs

## API Reference

### Core Commands

| Command | Parameters | Description |
|---------|------------|-------------|
| `click` | `id: string` | Simulate click on widget |
| `longpress` | `id: string, ms: int` | Extended press simulation |
| `swipe` | `x1, y1, x2, y2: int` | Gesture simulation with visual feedback |
| `screenshot` | - | Capture current UI state |
| `get_state` | `id: string` | Retrieve widget properties |
| `wait` | `ms: int` | Execution delay |

### Python Client API

```python
class LVGLTestClient:
    def connect() -> bool
    def click(widget_id: str) -> bool
    def longpress(widget_id: str, duration_ms: int = 1000) -> bool
    def swipe(x1: int, y1: int, x2: int, y2: int) -> bool
    def screenshot(save_path: str = None) -> bytes
    def get_state(widget_id: str) -> str
    def wait(duration_ms: int = 100) -> bool
```

### Widget Registry

The smartwatch UI includes the following interactive elements:

**Main Screen**
- `lbl_time`: Current time display
- `lbl_date`: Date information
- `lbl_battery`: Battery percentage
- `lbl_bpm`: Heart rate display
- `btn_heart`: Heart rate button
- `btn_activity`: Activity/steps button

**Heart Rate Screen**
- `lbl_hr_value`: Current heart rate value
- `lbl_hr_instruction`: Measurement instructions
- `hr_measure_area`: Long press area for measurements
- `hr_screen`: Background for navigation

**Activity Screen**
- `lbl_steps_count`: Step counter
- `lbl_calories`: Calories burned
- `activity_screen`: Background with swipe support

## Configuration

### Server Configuration

The automation server uses these default settings:

```bash
TCP_PORT=12345              # Server listen port
BIND_ADDRESS=127.0.0.1      # Local bind address  
CONNECTION_TIMEOUT=30       # Command timeout (seconds)
WINDOW_SIZE=480x480         # UI window dimensions
```

### Test Configuration

Create `pytest.ini` in your test directory:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (>5 seconds)
    integration: marks tests as integration tests
    swipe: marks tests that require swipe gestures
```

## Running Tests

### Quick Connection Test
```bash
cd python-client/tests
python test_connection_check.py
```

### Full Test Suite
```bash
cd python-client
pytest tests/test_simple_demo.py -v -s
```

### Individual Test Categories
```bash
# Basic UI validation
pytest tests/test_simple_demo.py::TestUIAutomation::test_01_main_watch_screen_validation -v

# Heart rate measurement workflow
pytest tests/test_simple_demo.py::TestUIAutomation::test_03_heart_rate_measurement_cycle -v

# Swipe gesture functionality
pytest tests/test_simple_demo.py::TestUIAutomation::test_05_swipe_functionality_validation -v
```

## Development

### Building from Source

```bash
# Clone the repository with submodules
git clone --recursive https://github.com/barkleyli/LVGL-UI-Automation-Framework.git
cd lvgl-ui-automation

# Build for development
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build . --config Debug
```

**Note**: This repository uses Git submodules for LVGL and LodePNG. Use `--recursive` flag or run `git submodule update --init --recursive` after cloning.

### Adding New UI Components

1. Register widgets in `src/ui_watch.c`
2. Add event handlers for interactions
3. Update widget registry with unique IDs
4. Create corresponding test cases

### Extending Test Framework

1. Add new test methods to `TestUIAutomation` class
2. Use descriptive naming: `test_##_feature_description`
3. Include proper setup/teardown with `reset_to_main_screen`
4. Add screenshots for visual validation
5. Use assertions with clear error messages

## Troubleshooting

### Common Issues

**Server Connection Failed**
- Ensure the automation server is running
- Check that port 12345 is not blocked by firewall
- Verify no other instances are using the port

**Tests Hang on Second Run**
- The framework includes automatic UI state reset
- If issues persist, restart the automation server
- Check console output for navigation error messages

**Screenshot Capture Failed**
- Ensure screenshots directory exists
- Check file permissions for write access
- Verify PNG encoding is working

**Swipe Gestures Not Working**
- Verify gesture events are enabled in LVGL configuration
- Check console for gesture detection debug messages
- Ensure no conflicting click handlers on swipe targets

**Build Fails - Third-Party Dependencies Missing**
- All dependencies are included in the repository
- If third_party/ directories appear empty after clone, check Git settings
- On Windows: ensure Git LFS is installed if large files are not downloading
- Verify CMake can find LVGL at third_party/lvgl and LodePNG at third_party/lodepng

### Debug Mode

Enable detailed logging by setting environment variables:

```bash
export LVGL_AUTOMATION_DEBUG=1
export LVGL_AUTOMATION_VERBOSE=1
./build/Release/lvgl-ui-automation.exe
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure all tests pass and follow the existing code style conventions.

## Acknowledgments

- LVGL team for the excellent graphics library
- SDL2 project for cross-platform windowing support
- pytest community for the testing framework
- Contributors who helped improve the swipe gesture system