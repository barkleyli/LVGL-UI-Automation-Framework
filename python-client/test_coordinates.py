#!/usr/bin/env python3
"""
Test script for coordinate-based LVGL automation commands.
This demonstrates the new click_at, mouse_move, and drag commands.
"""

import sys
import time
from pathlib import Path

# Add the client directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lvgl_client import LVGLTestClient

def test_coordinate_commands():
    """Test the new coordinate-based commands."""
    print("Testing coordinate-based commands...")
    
    with LVGLTestClient() as client:
        print("\n=== Testing CLICK_AT command ===")
        
        # Click at center of screen (assuming 480x480 display)
        print("1. Clicking at center of screen (240, 240)")
        result = client.click_at(240, 240)
        print(f"   Result: {'SUCCESS' if result else 'FAILED'}")
        
        time.sleep(1)
        
        # Click at top-left corner of screen
        print("2. Clicking at top-left (50, 50)")
        result = client.click_at(50, 50)
        print(f"   Result: {'SUCCESS' if result else 'FAILED'}")
        
        time.sleep(1)
        
        print("\n=== Testing MOUSE_MOVE command ===")
        
        # Move mouse to different positions
        positions = [(100, 100), (200, 200), (300, 300)]
        for x, y in positions:
            print(f"3. Moving mouse to ({x}, {y})")
            result = client.mouse_move(x, y)
            print(f"   Result: {'SUCCESS' if result else 'FAILED'}")
            time.sleep(0.5)
        
        print("\n=== Testing DRAG command ===")
        
        # Perform a drag gesture
        print("4. Dragging from (100, 200) to (300, 200)")
        result = client.drag(100, 200, 300, 200)
        print(f"   Result: {'SUCCESS' if result else 'FAILED'}")
        
        time.sleep(1)
        
        # Diagonal drag
        print("5. Diagonal drag from (50, 50) to (400, 400)")
        result = client.drag(50, 50, 400, 400)
        print(f"   Result: {'SUCCESS' if result else 'FAILED'}")
        
        print("\n=== Testing KEY event ===")
        
        # Test key events (some common key codes)
        key_codes = [13, 27, 32]  # Enter, Escape, Space
        for code in key_codes:
            print(f"6. Sending key code {code}")
            result = client.key_event(code)
            print(f"   Result: {'SUCCESS' if result else 'FAILED'}")
            time.sleep(0.5)
        
        print("\n=== Test completed ===")
        print("All coordinate-based commands have been tested!")

if __name__ == "__main__":
    try:
        test_coordinate_commands()
        print("\n[SUCCESS] All coordinate-based command tests completed!")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        print("\nMake sure the LVGL automation server is running:")
        print("  cd build/Release")
        print("  ./lvgl-ui-automation.exe")
        sys.exit(1)