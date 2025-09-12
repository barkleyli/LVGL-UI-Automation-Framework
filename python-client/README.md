# LVGL Test Client

Python client library for testing LVGL UI automation framework.

## Features

- Connect to LVGL automation server via TCP
- Execute UI commands (click, longpress, swipe)
- Capture screenshots for validation
- Automated test framework integration

## Usage

```python
from lvgl_client import LVGLTestClient

# Connect and test
with LVGLTestClient() as client:
    # Get widget state
    time_text = client.get_state("lbl_time")
    
    # Click a button
    client.click("heart_area")
    
    # Capture screenshot
    png_data = client.screenshot("test.png")
```

## Installation

```bash
pip install -e .
```

## Running Tests

```bash
pytest tests/
```