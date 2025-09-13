# LVGL UI Automation Framework

[![Build Status](https://github.com/barkleyli/LVGL-UI-Automation-Framework/actions/workflows/ci.yml/badge.svg)](https://github.com/barkleyli/LVGL-UI-Automation-Framework/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![LVGL](https://img.shields.io/badge/LVGL-9.x-blue.svg)](https://lvgl.io/)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)

A comprehensive testing and automation framework for LVGL-based user interfaces. Enables automated UI testing, screenshot capture, and interaction simulation for embedded and desktop applications. Includes a fully testable smartwatch demo application that demonstrates best practices for building LVGL UIs with testability from day one.

**Background**: LVGL's growing popularity in IoT and wearable devices created a need for robust UI automation solutions, but existing testing approaches were limited to basic coordinate clicking or required extensive manual setup. This framework bridges that gap by providing both immediate compatibility (coordinate-based) and production-grade reliability (widget-based) in a single, comprehensive solution.

## Features

### Core Automation Framework
- **Real-time UI Automation**: Click, longpress, and swipe gesture simulation
- **Hybrid Testing Approach**: Both widget ID-based and coordinate-based automation
- **Coordinate-Based Commands**: Direct pixel-level interaction for maximum compatibility
- **Screenshot Capture**: High-quality PNG screenshots for visual validation
- **Cross-platform Support**: Windows, Linux, and macOS compatibility
- **Python Test Framework**: Object-oriented testing with pytest integration
- **Network Interface**: JSON-based TCP communication protocol
- **Test Isolation**: Automatic UI state reset between test runs

### Testability Demonstration
- **Reference Implementation**: Complete smartwatch app with testability built-in
- **Widget Registry System**: Shows how to make LVGL widgets automation-friendly
- **Best Practices**: Demonstrates proper ID assignment and event handling
- **Real-world Example**: Multi-screen navigation, gestures, and state management

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
```

**Note**: This repository uses Git submodules for LVGL dependencies. The `--recursive` flag automatically initializes and clones the submodules. SDL2 development libraries are included for Windows support.

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
    
    # Widget-based interaction (semantic approach)
    client.click('btn_heart')
    client.wait(1000)  # Wait 1 second
    
    # Coordinate-based interaction (universal approach)
    client.click_at(240, 240)  # Click center of screen
    client.drag(100, 200, 300, 200)  # Horizontal drag
    client.mouse_move(150, 150)  # Move cursor
    
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

**Advanced Input Simulation System**
- **Hybrid Approach**: Both coordinate-based (like LVGL's built-in testing) AND semantic widget-based automation
- **Universal Compatibility**: Works with any LVGL application without code changes via coordinate commands
- **Enhanced Reliability**: Optional widget ID-based testing for production-grade test suites
- **Complete Gesture Support**: Click, longpress, drag, swipe, and mouse movement simulation
- **Real-time Visual Feedback**: Live panning during drag operations with configurable thresholds
- **Progressive Enhancement**: Start with coordinates, upgrade to semantic testing for better maintainability

**Test Isolation**
- Automatic UI state reset between test runs
- Multiple fallback methods for returning to main screen
- Robust error handling and recovery mechanisms
- Prevents test hanging on consecutive runs

## API Reference

### Core Commands

#### Widget-Based Commands (Semantic)
| Command | Parameters | Description |
|---------|------------|-------------|
| `click` | `id: string` | Simulate click on widget |
| `longpress` | `id: string, ms: int` | Extended press simulation |
| `get_state` | `id: string` | Retrieve widget properties |
| `set_text` | `id: string, text: string` | Set widget text content |

#### Coordinate-Based Commands (Universal)
| Command | Parameters | Description |
|---------|------------|-------------|
| `click_at` | `x: int, y: int` | Click at specific coordinates |
| `mouse_move` | `x: int, y: int` | Move mouse to coordinates |
| `drag` | `x1, y1, x2, y2: int` | Drag from one point to another |
| `swipe` | `x1, y1, x2, y2: int` | Gesture simulation with visual feedback |

#### General Commands
| Command | Parameters | Description |
|---------|------------|-------------|
| `key` | `code: int` | Send key event |
| `screenshot` | - | Capture current UI state |
| `wait` | `ms: int` | Execution delay |

### Python Client API

```python
class LVGLTestClient:
    # Connection
    def connect() -> bool
    
    # Widget-based methods (semantic)
    def click(widget_id: str) -> bool
    def longpress(widget_id: str, duration_ms: int = 1000) -> bool
    def get_state(widget_id: str) -> str
    def set_text(widget_id: str, text: str) -> bool
    
    # Coordinate-based methods (universal)
    def click_at(x: int, y: int) -> bool
    def mouse_move(x: int, y: int) -> bool
    def drag(x1: int, y1: int, x2: int, y2: int) -> bool
    def swipe(x1: int, y1: int, x2: int, y2: int) -> bool
    
    # General methods
    def key_event(key_code: int) -> bool
    def screenshot(save_path: str = None) -> bytes
    def wait(duration_ms: int = 100) -> bool
```

## Building Testable LVGL Applications

The included smartwatch application serves as a complete reference implementation, demonstrating how to build LVGL UIs with testability from the ground up.

### Key Testability Patterns Demonstrated

**1. Widget Registration Pattern**
```c
// Register widgets with unique IDs for automation
reg_widget("btn_heart", heart_button);
reg_widget("lbl_time", time_label);
reg_widget("main_screen", main_screen_obj);
```

**2. Event Handler Design**
```c
// Design event handlers to be automation-friendly
static void heart_button_event_handler(lv_event_t * e) {
    lv_event_code_t code = lv_event_get_code(e);
    if(code == LV_EVENT_CLICKED) {
        // Handle both manual and automated clicks
        show_screen(SCREEN_HEART_RATE);
    }
}
```

**3. State Management**
```c
// Make widget states readable for automation
void update_heart_rate_display(int bpm) {
    lv_label_set_text_fmt(lbl_hr_value, "%d BPM", bpm);
    // Widget state now accessible via get_state() command
}
```

### Widget Registry

The smartwatch demo includes the following testable elements:

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

**Note**: This repository uses Git submodules for LVGL. Use `--recursive` flag or run `git submodule update --init --recursive` after cloning.

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
- Verify CMake can find LVGL at third_party/lvgl

### Debug Mode

Enable detailed logging by setting environment variables:

```bash
export LVGL_AUTOMATION_DEBUG=1
export LVGL_AUTOMATION_VERBOSE=1
./build/Release/lvgl-ui-automation.exe
```

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

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
- STD stb_image_write for PNG processing
- Contributors who helped improve the swipe gesture system