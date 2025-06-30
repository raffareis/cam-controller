"""
Camera Test - OpenCV Webcam Capture Test

This script tests camera input from:
1. Built-in webcam (index 0, 1, 2...)
2. IP Webcam from phone (via URL)

Controls:
- 'q' or ESC: Quit
- 'c': Switch camera source
- 's': Save current frame
- 'i': Show camera info
"""

import cv2
import numpy as np
import sys
import time
from typing import Optional, Union

class CameraCapture:
    def __init__(self):
        self.cap: Optional[cv2.VideoCapture] = None
        self.camera_sources = [
            # Built-in webcam sources
            {"name": "Default Camera (0)", "source": 0, "type": "webcam"},
            {"name": "Camera 1", "source": 1, "type": "webcam"},
            {"name": "Camera 2", "source": 2, "type": "webcam"},
            # IP Webcam sources (common URLs)
            {"name": "IP Webcam (Default Port)", "source": "http://192.168.1.100:8080/video", "type": "ip"},
            {"name": "IP Webcam (Alt Port)", "source": "http://192.168.1.100:4747/video", "type": "ip"},
            {"name": "DroidCam", "source": "http://192.168.1.100:4747/mjpegfeed", "type": "ip"},
        ]
        self.current_source_index = 0
        self.frame_count = 0
        self.fps_counter = time.time()
        
    def connect_camera(self, source: Union[int, str]) -> bool:
        """Connect to camera source"""
        try:
            if self.cap:
                self.cap.release()
            
            print(f"Attempting to connect to: {source}")
            self.cap = cv2.VideoCapture(source)
            
            # Set some common properties for better performance
            if isinstance(source, int):  # Webcam
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Test if we can read a frame
            ret, frame = self.cap.read()
            if ret:
                print(f"✅ Successfully connected to camera: {source}")
                print(f"   Frame size: {frame.shape[1]}x{frame.shape[0]}")
                return True
            else:
                print(f"❌ Could not read frame from: {source}")
                return False
                
        except Exception as e:
            print(f"❌ Error connecting to camera {source}: {e}")
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get current frame from camera"""
        if not self.cap:
            return None
        
        ret, frame = self.cap.read()
        if ret:
            self.frame_count += 1
            return frame
        return None
    
    def calculate_fps(self) -> float:
        """Calculate current FPS"""
        current_time = time.time()
        elapsed = current_time - self.fps_counter
        if elapsed >= 1.0:  # Update every second
            fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_counter = current_time
            return fps
        return 0.0
    
    def switch_camera(self) -> bool:
        """Switch to next camera source"""
        self.current_source_index = (self.current_source_index + 1) % len(self.camera_sources)
        source_info = self.camera_sources[self.current_source_index]
        print(f"\nSwitching to: {source_info['name']}")
        return self.connect_camera(source_info['source'])
    
    def get_current_source_info(self) -> dict:
        """Get info about current camera source"""
        return self.camera_sources[self.current_source_index]
    
    def release(self):
        """Release camera resources"""
        if self.cap:
            self.cap.release()
            self.cap = None

def show_instructions():
    """Show usage instructions"""
    print("\n" + "="*50)
    print("Camera Test - Controls:")
    print("="*50)
    print("'q' or ESC  - Quit")
    print("'c'         - Switch camera source")
    print("'s'         - Save current frame")
    print("'i'         - Show camera info")
    print("'h'         - Show this help")
    print("="*50)

def show_camera_info(camera: CameraCapture):
    """Display camera information"""
    if not camera.cap:
        print("No camera connected")
        return
    
    source_info = camera.get_current_source_info()
    print(f"\n📹 Current Camera: {source_info['name']}")
    print(f"   Type: {source_info['type']}")
    print(f"   Source: {source_info['source']}")
    
    # Try to get camera properties
    try:
        width = int(camera.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(camera.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = camera.cap.get(cv2.CAP_PROP_FPS)
        print(f"   Resolution: {width}x{height}")
        print(f"   Target FPS: {fps}")
    except:
        print("   Could not read camera properties")

def setup_ip_webcam_instructions():
    """Show IP Webcam setup instructions"""
    print("\n" + "="*60)
    print("📱 IP Webcam Setup Instructions:")
    print("="*60)
    print("1. Install 'IP Webcam' app on your Android phone")
    print("2. Open the app and click 'Start server'")
    print("3. Note the IP address shown (e.g., 192.168.1.100:8080)")
    print("4. Edit this script and update the IP addresses in camera_sources")
    print("5. Make sure your phone and computer are on the same WiFi")
    print("\nFor iPhone:")
    print("- Use 'EpocCam' or similar apps")
    print("- Follow similar steps")
    print("="*60)

def main():
    print("Camera Test - Starting...")
    
    # Show setup instructions
    setup_ip_webcam_instructions()
    show_instructions()
    
    camera = CameraCapture()
    
    # Try to connect to first available camera
    connected = False
    for i, source_info in enumerate(camera.camera_sources):
        camera.current_source_index = i
        if camera.connect_camera(source_info['source']):
            connected = True
            break
    
    if not connected:
        print("\n❌ Could not connect to any camera source!")
        print("Please check:")
        print("1. Webcam is connected and not in use by other apps")
        print("2. IP Webcam app is running on phone (for phone camera)")
        print("3. IP addresses in the script match your phone's IP")
        input("Press Enter to exit...")
        return
    
    print(f"\n🎥 Camera connected! Press 'h' for help.")
    
    # Main camera loop
    fps_display = 0.0
    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                print("❌ Lost camera connection")
                break
            
            # Calculate FPS
            current_fps = camera.calculate_fps()
            if current_fps > 0:
                fps_display = current_fps
            
            # Add info overlay
            source_info = camera.get_current_source_info()
            cv2.putText(frame, f"Source: {source_info['name']}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"FPS: {fps_display:.1f}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Press 'h' for help", (10, frame.shape[0] - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show frame
            cv2.imshow('Camera Test - Para Controller POC', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == 27:  # 'q' or ESC
                break
            elif key == ord('c'):  # Switch camera
                print("Switching camera...")
                if not camera.switch_camera():
                    print("Failed to switch camera, trying next...")
                    continue
            elif key == ord('s'):  # Save frame
                filename = f"camera_test_frame_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"📸 Frame saved as: {filename}")
            elif key == ord('i'):  # Show info
                show_camera_info(camera)
            elif key == ord('h'):  # Show help
                show_instructions()
                
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Camera test ended.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        input("Press Enter to exit...") 