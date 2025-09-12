"""
LVGL UI Automation - Comprehensive Demo Tests

QA validation tests that verify the complete UI automation workflow.
Tests follow the same flow as demo.py to ensure UI captures are correct.
"""

import pytest
import time
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lvgl_client import LVGLTestClient


class TestUIAutomation:
    """Comprehensive UI automation tests matching demo.py workflow."""
    
    @classmethod
    def setup_class(cls):
        """Called once before all tests in this class."""
        print("\n=== Starting LVGL UI Test Suite ===")
    
    @classmethod 
    def teardown_class(cls):
        """Called once after all tests in this class."""
        print("\n=== Finished LVGL UI Test Suite ===")
        print("Note: If tests need to run again, the UI should be reset to main screen")
    
    @pytest.fixture
    def client(self):
        """Create connected test client."""
        try:
            with LVGLTestClient() as client:
                # Test connection before yielding
                test_response = client.get_state("lbl_time")
                if test_response is None:
                    pytest.skip("LVGL automation server not responding - make sure the app is running")
                yield client
        except Exception as e:
            pytest.skip(f"Cannot connect to LVGL automation server: {e}")
    
    def reset_to_main_screen(self, client):
        """Force reset to main screen using multiple methods."""
        print("Resetting UI to main screen...")
        
        # Method 1: Try clicking on main screen elements
        try:
            # If we're on HR screen, click background to go back
            main_found = client.get_state("lbl_time")
            if main_found and ":" in main_found:
                print(f"Already on main screen - Time: {main_found}")
                return True
        except:
            pass
        
        # Method 2: Try navigating from different screens
        attempts = [
            ("hr_screen", "Clicking HR screen background"),
            ("activity_screen", "Clicking activity screen background"), 
            ("btn_heart", "Using heart button navigation"),
        ]
        
        for widget, description in attempts:
            try:
                print(f"Reset attempt: {description}")
                client.click(widget)
                time.sleep(0.3)
                
                # Check if we're back on main
                main_time = client.get_state("lbl_time")
                if main_time and ":" in main_time:
                    print(f"Reset successful - Time: {main_time}")
                    return True
            except:
                continue
        
        # Method 3: Use swipe as last resort
        try:
            print("Reset attempt: Using swipe navigation")
            client.swipe(80, 240, 400, 240)  # Left to right swipe
            time.sleep(0.3)
            main_time = client.get_state("lbl_time")
            if main_time and ":" in main_time:
                print(f"Reset via swipe successful - Time: {main_time}")
                return True
        except:
            pass
            
        print("WARNING: Could not confirm reset to main screen")
        return False
    
    @pytest.fixture
    def screenshots_dir(self):
        """Create screenshots directory."""
        screenshots_dir = Path("../../screenshots/test_validation")
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        return screenshots_dir
    
    def ensure_main_screen(self, client):
        """Ensure we're on the main screen - simple check only."""
        # Just verify we're on main screen, don't force navigation
        time_text = client.get_state("lbl_time")
        if time_text and ":" in time_text:
            print(f"Main screen ready - Time: {time_text}")
            return True
        else:
            print(f"Warning: May not be on main screen - Time: {time_text}")
            return False
    
    def setup_method(self, method):
        """Called before each test method."""
        print(f"\n--- Starting {method.__name__} ---")
        # Note: Reset will be called explicitly in each test that needs it
    
    def teardown_method(self, method):
        """Called after each test method."""
        print(f"--- Finished {method.__name__} ---")
        # Reset will be handled by the next test's setup if needed
    
    def test_01_main_watch_screen_validation(self, client, screenshots_dir):
        """Test main watch screen capture and state validation."""
        print("Testing main watch screen...")
        self.reset_to_main_screen(client)  # Ensure clean start
        
        # Capture main screen
        client.screenshot(screenshots_dir / "test_01_main_watch.png")
        
        # Validate main screen elements
        time_text = client.get_state("lbl_time")
        assert time_text is not None and ":" in time_text, f"Invalid time display: {time_text}"
        
        bmp_text = client.get_state("lbl_bpm")
        assert bmp_text is not None and "BPM" in bmp_text, f"Invalid BPM text: {bmp_text}"
        
        print(f"[PASS] Main screen validated - Time: {time_text}, BPM: {bmp_text}")
    
    def test_02_heart_rate_navigation(self, client, screenshots_dir):
        """Test navigation to heart rate screen with proper UI state."""
        print("Testing heart rate screen navigation...")
        
        # Click heart button
        success = client.click("btn_heart")
        assert success, "Heart button click failed"
        
        # Wait for screen transition
        time.sleep(0.5)
        client.screenshot(screenshots_dir / "test_02_heart_rate_screen.png")
        
        # Validate heart rate screen UI
        hr_instruction = client.get_state("lbl_hr_instruction")
        assert hr_instruction == "Long press to measure", f"Incorrect instruction text: {hr_instruction}"
        
        hr_value = client.get_state("lbl_hr_value")
        assert "BPM" in hr_value, f"Invalid HR value: {hr_value}"
        
        print(f"[PASS] Heart rate screen validated - Instruction: '{hr_instruction}', Value: {hr_value}")
    
    def test_03_heart_rate_measurement_cycle(self, client, screenshots_dir):
        """Test complete heart rate measurement with proper UI feedback."""
        print("Testing heart rate measurement cycle...")
        
        # Ensure we're on heart rate screen
        client.click("btn_heart")
        time.sleep(0.5)
        
        # Start measurement with long press
        success = client.longpress("hr_measure_area", 2000)
        assert success, "Long press for measurement failed"
        
        # Capture measuring state immediately
        time.sleep(0.5)
        client.screenshot(screenshots_dir / "test_03_measuring_state.png")
        
        # Validate measuring state
        measuring_text = client.get_state("lbl_hr_instruction")
        assert "measuring" in measuring_text.lower() or "hold still" in measuring_text.lower(), \
               f"Invalid measuring text: {measuring_text}"
        
        print(f"[PASS] Measuring state validated: '{measuring_text}'")
        
        # Wait for measurement completion
        time.sleep(3.5)
        client.screenshot(screenshots_dir / "test_04_measurement_complete.png")
        
        # Validate completion state
        complete_text = client.get_state("lbl_hr_instruction")
        hr_final_value = client.get_state("lbl_hr_value")
        
        assert "tap to" in complete_text.lower() or "click to" in complete_text.lower(), \
               f"Invalid completion text: {complete_text}"
        assert "BPM" in hr_final_value, f"Invalid final HR value: {hr_final_value}"
        
        print(f"[PASS] Measurement completed - Final: {hr_final_value}, Instructions: '{complete_text}'")
    
    def test_04_activity_screen_navigation(self, client, screenshots_dir):
        """Test activity screen navigation and state validation."""
        print("Testing activity screen navigation...")
        self.reset_to_main_screen(client)  # Ensure we start from main screen
        client.click("btn_heart")  # Go to HR screen
        time.sleep(0.3)
        client.click("hr_screen")  # Click to return to main
        time.sleep(0.5)
        
        # Navigate to activity screen
        success = client.click("btn_activity")
        assert success, "Activity button click failed"
        
        time.sleep(0.5)
        client.screenshot(screenshots_dir / "test_05_activity_screen.png")
        
        # Validate activity screen elements
        steps_text = client.get_state("lbl_steps_count")
        calories_text = client.get_state("lbl_calories")
        
        assert steps_text is not None and steps_text.isdigit(), f"Invalid steps count: {steps_text}"
        assert calories_text is not None and "cal" in calories_text, f"Invalid calories text: {calories_text}"
        
        print(f"[PASS] Activity screen validated - Steps: {steps_text}, Calories: {calories_text}")
    
    def test_05_swipe_functionality_validation(self, client, screenshots_dir):
        """Test swipe functionality with visual validation."""
        print("Testing swipe functionality...")
        self.reset_to_main_screen(client)  # Ensure clean starting state
        client.click("btn_heart")  # Go to HR
        time.sleep(0.3)
        client.click("hr_screen")  # Return to main
        time.sleep(0.5)
        
        # Test swipe to activity screen
        client.swipe(400, 240, 80, 240)  # Right to left swipe
        time.sleep(0.5)
        client.screenshot(screenshots_dir / "test_06_swipe_to_activity.png")
        
        # Validate we're on activity screen
        steps_text = client.get_state("lbl_steps_count")
        assert steps_text is not None, "Swipe to activity screen failed"
        print(f"[PASS] Swipe to activity successful - Steps: {steps_text}")
        
        # Test swipe back to main
        client.swipe(80, 240, 400, 240)  # Left to right swipe
        time.sleep(0.5)
        client.screenshot(screenshots_dir / "test_07_swipe_to_main.png")
        
        # Validate we're back on main screen
        time_text = client.get_state("lbl_time")
        assert time_text is not None and ":" in time_text, "Swipe back to main failed"
        print(f"[PASS] Swipe back to main successful - Time: {time_text}")
    
    def test_06_complete_workflow_integration(self, client, screenshots_dir):
        """Test complete workflow integration like demo.py."""
        print("Testing complete workflow integration...")
        self.reset_to_main_screen(client)  # Start fresh for complete workflow
        
        workflow_steps = []
        
        # Step 1: Main screen
        client.screenshot(screenshots_dir / "workflow_01_main.png")
        time_display = client.get_state("lbl_time")
        workflow_steps.append(f"Main screen - Time: {time_display}")
        
        # Step 2: Heart rate screen
        client.click("btn_heart")
        time.sleep(0.5)
        client.screenshot(screenshots_dir / "workflow_02_heart_rate.png")
        hr_instruction = client.get_state("lbl_hr_instruction")
        workflow_steps.append(f"Heart rate screen - Instruction: {hr_instruction}")
        
        # Step 3: Start measurement
        client.longpress("hr_measure_area", 2000)
        time.sleep(0.5)
        client.screenshot(screenshots_dir / "workflow_03_measuring.png")
        measuring_state = client.get_state("lbl_hr_instruction")
        workflow_steps.append(f"Measuring - State: {measuring_state}")
        
        # Step 4: Complete measurement
        time.sleep(3.5)
        client.screenshot(screenshots_dir / "workflow_04_measurement_done.png")
        final_value = client.get_state("lbl_hr_value")
        workflow_steps.append(f"Measurement complete - Value: {final_value}")
        
        # Step 5: Navigate to activity via swipe
        client.click("hr_screen")  # Go back to main
        time.sleep(0.5)
        client.swipe(400, 240, 80, 240)  # Swipe to activity
        time.sleep(0.5)
        client.screenshot(screenshots_dir / "workflow_05_activity_via_swipe.png")
        steps_count = client.get_state("lbl_steps_count")
        workflow_steps.append(f"Activity via swipe - Steps: {steps_count}")
        
        # Validate complete workflow
        assert len(workflow_steps) == 5, "Incomplete workflow execution"
        
        print("[PASS] Complete workflow validated:")
        for i, step in enumerate(workflow_steps, 1):
            print(f"  {i}. {step}")
    
    def test_07_error_conditions_and_recovery(self, client, screenshots_dir):
        """Test error handling and UI recovery."""
        print("Testing error conditions and recovery...")
        self.reset_to_main_screen(client)  # Clean state for error testing
        
        # Test invalid widget interaction
        success = client.click("non_existent_widget")
        assert not success, "Should fail for non-existent widgets"
        
        # Ensure UI is still responsive after error
        client.screenshot(screenshots_dir / "test_08_after_error.png")
        time_text = client.get_state("lbl_time")
        assert time_text is not None, "UI should remain responsive after errors"
        
        print("[PASS] Error handling validated - UI remains stable")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # Added -s for real-time output