"""
LVGL UI Test Client

A Python client for automating the LVGL smartwatch simulator.
Provides functions for clicking widgets, taking screenshots, and comparing images.
"""

import socket
import json
import time
import subprocess
import os
import sys
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

from PIL import Image
import numpy as np


class LVGLTestClient:
    """Client for communicating with LVGL test simulator."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 12345, timeout: float = 30.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to the LVGL simulator."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"Connected to LVGL simulator at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to {self.host}:{self.port}: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the simulator."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.connected = False
        print("Disconnected from LVGL simulator")
    
    def _send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON command and receive response."""
        if not self.connected or not self.socket:
            raise RuntimeError("Not connected to simulator")
        
        # Send command
        cmd_json = json.dumps(command) + "\n"
        self.socket.send(cmd_json.encode('utf-8'))
        print(f"Sent: {command}")
        
        # Receive response
        response_line = self._recv_line()
        if not response_line:
            raise RuntimeError("No response received")
        
        try:
            response = json.loads(response_line)
            print(f"Received: {response}")
            return response
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response: {response_line}") from e
    
    def _recv_line(self) -> str:
        """Receive a line of text from the socket."""
        buffer = b""
        while True:
            chunk = self.socket.recv(1)
            if not chunk:
                break
            if chunk == b"\n":
                break
            buffer += chunk
        return buffer.decode('utf-8').strip()
    
    def _recv_exact(self, size: int) -> bytes:
        """Receive exact number of bytes."""
        buffer = b""
        while len(buffer) < size:
            chunk = self.socket.recv(size - len(buffer))
            if not chunk:
                raise RuntimeError("Connection closed while receiving data")
            buffer += chunk
        return buffer
    
    def click(self, widget_id: str) -> bool:
        """Click a widget by ID."""
        try:
            response = self._send_command({"cmd": "click", "id": widget_id})
            return response.get("status") == "ok"
        except Exception as e:
            print(f"Click failed: {e}")
            return False
    
    def longpress(self, widget_id: str, duration_ms: int = 1000) -> bool:
        """Long press a widget by ID."""
        try:
            response = self._send_command({
                "cmd": "longpress", 
                "id": widget_id, 
                "ms": duration_ms
            })
            return response.get("status") == "ok"
        except Exception as e:
            print(f"Longpress failed: {e}")
            return False
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Perform swipe gesture."""
        try:
            response = self._send_command({
                "cmd": "swipe",
                "x1": x1, "y1": y1,
                "x2": x2, "y2": y2
            })
            return response.get("status") == "ok"
        except Exception as e:
            print(f"Swipe failed: {e}")
            return False
    
    def key_event(self, key_code: int) -> bool:
        """Send key event."""
        try:
            response = self._send_command({"cmd": "key", "code": key_code})
            return response.get("status") == "ok"
        except Exception as e:
            print(f"Key event failed: {e}")
            return False
    
    def get_state(self, widget_id: str) -> Optional[str]:
        """Get widget state (text content)."""
        try:
            response = self._send_command({"cmd": "get_state", "id": widget_id})
            if response.get("status") == "ok":
                return response.get("text")
            return None
        except Exception as e:
            print(f"Get state failed: {e}")
            return None
    
    def set_text(self, widget_id: str, text: str) -> bool:
        """Set widget text content."""
        try:
            response = self._send_command({
                "cmd": "set_text", 
                "id": widget_id, 
                "text": text
            })
            return response.get("status") == "ok"
        except Exception as e:
            print(f"Set text failed: {e}")
            return False
    
    def wait(self, duration_ms: int = 100) -> bool:
        """Wait for specified duration."""
        try:
            response = self._send_command({"cmd": "wait", "ms": duration_ms})
            return response.get("status") == "ok"
        except Exception as e:
            print(f"Wait failed: {e}")
            return False
    
    def screenshot(self, save_path: Optional[str] = None) -> Optional[bytes]:
        """Take a screenshot and optionally save to file."""
        try:
            response = self._send_command({"cmd": "screenshot"})
            
            if response.get("status") != "ok":
                print(f"Screenshot command failed: {response}")
                return None
            
            # Check if it's raw framebuffer data
            if response.get("type") == "screenshot_raw":
                return self._handle_raw_screenshot(response, save_path)
            elif response.get("type") == "screenshot":
                # Legacy PNG handling
                return self._handle_png_screenshot(response, save_path)
            else:
                print(f"Unexpected response type: {response.get('type')}")
                return None
            
        except Exception as e:
            print(f"Screenshot failed: {e}")
            return None
    
    def _handle_raw_screenshot(self, response: Dict[str, Any], save_path: Optional[str] = None) -> Optional[bytes]:
        """Handle raw framebuffer screenshot data."""
        # Get format information
        width = response.get("width", 0)
        height = response.get("height", 0)
        format_str = response.get("format", "RGB")
        raw_len = response.get("len", 0)
        
        if width <= 0 or height <= 0 or raw_len <= 0:
            print(f"Invalid raw screenshot parameters: {width}x{height}, {raw_len} bytes")
            return None
        
        print(f"Receiving raw screenshot: {width}x{height} {format_str}, {raw_len} bytes")
        
        # Receive raw framebuffer data
        raw_data = self._recv_exact(raw_len)
        if len(raw_data) != raw_len:
            print(f"Incomplete raw data received: {len(raw_data)}/{raw_len} bytes")
            return None
        
        # Convert raw data to PNG using PIL
        try:
            from PIL import Image
            import io
            
            # Create PIL Image from raw bytes
            if format_str == "RGB":
                img = Image.frombytes("RGB", (width, height), raw_data)
            elif format_str == "RGBA":
                img = Image.frombytes("RGBA", (width, height), raw_data)
            else:
                print(f"Unsupported format: {format_str}")
                return None
            
            # Convert to PNG bytes
            png_buffer = io.BytesIO()
            img.save(png_buffer, format='PNG')
            png_data = png_buffer.getvalue()
            
            print(f"Converted raw data to PNG: {len(png_data)} bytes")
            
            # Save to file if requested
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(png_data)
                print(f"Screenshot saved to {save_path}")
            
            return png_data
            
        except ImportError:
            print("PIL (Pillow) is required for raw screenshot conversion")
            return None
        except Exception as e:
            print(f"Failed to convert raw data to PNG: {e}")
            return None
    
    def _handle_png_screenshot(self, response: Dict[str, Any], save_path: Optional[str] = None) -> Optional[bytes]:
        """Handle legacy PNG screenshot data."""
        png_len = response.get("len", 0)
        if png_len <= 0:
            print("Invalid PNG length")
            return None
        
        png_data = self._recv_exact(png_len)
        print(f"Received PNG screenshot: {len(png_data)} bytes")
        
        # Save to file if requested
        if save_path:
            with open(save_path, 'wb') as f:
                f.write(png_data)
            print(f"Screenshot saved to {save_path}")
        
        return png_data
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


class SimulatorProcess:
    """Manages the LVGL simulator process."""
    
    def __init__(self, executable_path: str):
        self.executable_path = Path(executable_path)
        self.process: Optional[subprocess.Popen] = None
        
    def start(self, wait_for_ready: float = 5.0) -> bool:
        """Start the simulator process."""
        if not self.executable_path.exists():
            print(f"Simulator executable not found: {self.executable_path}")
            return False
        
        try:
            # Set up environment
            env = os.environ.copy()
            # Allow GUI mode by default for UI testing
            # Only use headless mode if explicitly requested via environment variable
            if os.getenv('LVGL_HEADLESS') == '1':
                env['SDL_VIDEODRIVER'] = 'dummy'  # Use dummy video driver for headless mode
                env['SDL_AUDIODRIVER'] = 'dummy'  # Use dummy audio driver
            
            # Start the simulator process
            # For debugging, let's not capture output so we can see debug messages
            self.process = subprocess.Popen(
                [str(self.executable_path)],
                env=env
            )
            
            print(f"Started simulator process (PID: {self.process.pid})")
            
            # Wait for the process to be ready
            print(f"Waiting {wait_for_ready} seconds for simulator to initialize...")
            time.sleep(wait_for_ready)
            
            # Check if process is still running
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                print(f"Simulator process exited early with return code: {self.process.returncode}")
                if stdout:
                    print(f"STDOUT: {stdout}")
                if stderr:
                    print(f"STDERR: {stderr}")
                return False
            
            print("Simulator appears to be ready")
            return True
            
        except Exception as e:
            print(f"Failed to start simulator: {e}")
            return False
    
    def stop(self):
        """Stop the simulator process."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            except Exception as e:
                print(f"Error stopping simulator: {e}")
            finally:
                self.process = None
            print("Simulator process stopped")
    
    def is_running(self) -> bool:
        """Check if simulator is running."""
        return self.process is not None and self.process.poll() is None
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Image comparison functionality removed for simplified demo approach


# Convenience functions for pytest
def create_client(host: str = "127.0.0.1", port: int = 12345) -> LVGLTestClient:
    """Create and connect to LVGL test client."""
    client = LVGLTestClient(host, port)
    if not client.connect():
        raise RuntimeError(f"Failed to connect to simulator at {host}:{port}")
    return client


def find_simulator_executable() -> Optional[Path]:
    """Find the simulator executable in common locations."""
    possible_paths = [
        Path("../build/lvgl-ui-test-proto"),
        Path("../build/lvgl-ui-test-proto.exe"),
        Path("../build/Release/lvgl-ui-test-proto.exe"),
        Path("../build/Debug/lvgl-ui-test-proto.exe"),
        Path("../../build/lvgl-ui-test-proto"),
        Path("../../build/lvgl-ui-test-proto.exe"),
        Path("../../build/Release/lvgl-ui-test-proto.exe"),
        Path("../../build/Debug/lvgl-ui-test-proto.exe"),
        Path("./lvgl-ui-test-proto"),
        Path("./lvgl-ui-test-proto.exe")
    ]
    
    for path in possible_paths:
        if path.exists():
            return path.resolve()
    
    return None


if __name__ == "__main__":
    # Test the client connection
    print("LVGL Test Client")
    print("================")
    
    # Try to connect to simulator
    with LVGLTestClient() as client:
        if not client.connected:
            print("Failed to connect. Make sure the simulator is running.")
            sys.exit(1)
        
        print("Connected! Testing basic commands...")
        
        # Test basic commands
        client.wait(500)
        print("Wait command: OK")
        
        # Try to click heart button
        if client.click("btn_heart"):
            print("Heart button click: OK")
        else:
            print("Heart button click: FAILED")
        
        client.wait(1000)
        
        # Try to get BPM state
        bpm = client.get_state("lbl_bpm")
        if bpm:
            print(f"BPM state: {bpm}")
        else:
            print("BPM state: FAILED")
        
        # Take a screenshot
        screenshot_data = client.screenshot("test_screenshot.png")
        if screenshot_data:
            print(f"Screenshot: OK ({len(screenshot_data)} bytes)")
        else:
            print("Screenshot: FAILED")
        
        print("Basic tests completed!")