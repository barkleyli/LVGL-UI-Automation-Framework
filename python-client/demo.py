#!/usr/bin/env python3
"""
LVGL UI Automation Framework - Simple Demo

This demo showcases the key automation capabilities:
- Screenshot capture
- Widget interaction
- State monitoring
- Basic UI workflow testing

Perfect for marketing materials and quick demonstrations.
"""

import time
from pathlib import Path
from lvgl_client import LVGLTestClient

def main():
    """Run a simple demonstration of the automation framework."""
    print("LVGL UI Automation Framework - Demo")
    print("=" * 40)
    
    # Create screenshots directory
    screenshots_dir = Path("../screenshots/demo")
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    with LVGLTestClient() as client:
        print("* Connected to automation server")
        
        # Demo 1: Main Watch Screen
        print("\n1. Capturing main watch screen...")
        client.screenshot(screenshots_dir / "01_main_watch_screen.png")
        bmp_text = client.get_state("lbl_bpm")
        print(f"   Main screen heart rate: {bmp_text}")
        
        # Demo 2: Click Heart Button (switches to heart rate screen)
        print("\n2. Clicking heart rate button...")
        client.click("btn_heart")
        time.sleep(0.5)  # Allow screen transition
        client.screenshot(screenshots_dir / "02_heart_rate_screen.png")
        print("   Heart rate screen captured with 'Long press to measure'")
        
        # Demo 3: Long press center circle for measurement
        print("\n3. Long press center circle for heart rate measurement...")
        client.longpress("hr_measure_area", 2000)  # Long press measurement area
        time.sleep(0.5)  # Allow measuring state to display
        client.screenshot(screenshots_dir / "03_heart_measuring.png")
        measuring_text = client.get_state("lbl_hr_instruction")
        print(f"   Measurement state: {measuring_text}")
        
        # Wait for measurement to complete (3 seconds) and capture final state
        print("   Waiting for measurement to complete...")
        time.sleep(3.5)  # Wait for background process to complete
        client.screenshot(screenshots_dir / "04_measurement_complete.png")
        complete_text = client.get_state("lbl_hr_instruction")
        hr_value = client.get_state("lbl_hr_value")
        print(f"   Measurement complete: {hr_value} - {complete_text}")
        
        # Tap to go back to main screen
        print("   Tapping to return to main screen...")
        client.click("hr_screen")  # Click anywhere to go back
        time.sleep(0.5)
        
        # Demo 5: Click Steps to go to Activity Screen  
        print("\n5. Clicking steps to go to activity screen...")
        client.click("btn_activity")  # Click steps/activity button
        time.sleep(0.5)
        client.screenshot(screenshots_dir / "05_activity_screen.png")
        steps = client.get_state("lbl_steps_count")
        print(f"   Activity screen steps: {steps}")
        
        # Demo 6: Swipe functionality - swipe back to main
        print("\n6. Testing swipe functionality - returning to main...")
        client.swipe(80, 240, 400, 240)  # Left to right swipe (activity -> main)
        time.sleep(0.5)
        client.screenshot(screenshots_dir / "06_swipe_to_main.png")
        print("   Swipe back to main screen captured")
        
        # Demo 7: Swipe to activity screen again to show both directions
        print("\n7. Swipe to activity screen to demonstrate swipe navigation...")
        client.swipe(400, 240, 80, 240)  # Right to left swipe (main -> activity)
        time.sleep(0.5)
        client.screenshot(screenshots_dir / "07_swipe_to_activity.png")
        print("   Swipe to activity screen captured")
        
        # Final: Return to main screen
        print("\n8. Final: Return to main screen...")
        client.swipe(80, 240, 400, 240)  # Left to right swipe back to main
        time.sleep(0.5)
        client.screenshot(screenshots_dir / "08_final_main.png")
        print("   Demo completed - back to main screen")
        
        print("\n* Demo completed successfully!")
        print(f"* Screenshots saved to: {screenshots_dir}")
        print("\nGenerated demo screenshots:")
        for i, name in enumerate([
            "01_main_watch_screen.png - Main watch face with time and heart rate",
            "02_heart_rate_screen.png - Heart rate screen with 'Long press to measure'", 
            "03_heart_measuring.png - Active heart rate measurement 'Hold still... measuring'",
            "04_measurement_complete.png - Heart rate measurement completed with BPM value",
            "05_activity_screen.png - Activity tracking screen with steps and calories",
            "06_swipe_to_main.png - Swipe navigation from activity back to main screen",
            "07_swipe_to_activity.png - Swipe navigation from main to activity screen", 
            "08_final_main.png - Final state back to main watch screen"
        ], 1):
            print(f"  {i}. {name}")

if __name__ == "__main__":
    main()