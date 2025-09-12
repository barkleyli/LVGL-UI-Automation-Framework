#!/usr/bin/env python3
"""
Quick connection test to verify LVGL automation server is running.
Run this before running the full test suite.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lvgl_client import LVGLTestClient

def test_connection():
    """Test if we can connect to the automation server."""
    try:
        print("Testing connection to LVGL automation server...")
        
        with LVGLTestClient() as client:
            print("[PASS] Connected successfully!")
            
            # Test basic operations
            time_text = client.get_state("lbl_time")
            print(f"[TEST] Time display: {time_text}")
            
            if time_text and ":" in time_text:
                print("[PASS] Server is responding correctly")
                return True
            else:
                print("[FAIL] Server response invalid")
                return False
                
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        print("\nTo fix this:")
        print("1. Make sure the LVGL automation app is running:")
        print("   cd C:/Users/barkl/Documents/freertos_lgvl_automation")
        print("   ./build/Release/lvgl-ui-automation.exe")
        print("2. Wait for 'Ready for automation commands' message")
        print("3. Then run the tests")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)