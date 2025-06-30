"""
Pink Glove Controller - Camera-based Virtual Joystick

This application combines:
1. Camera input (webcam or phone via IP Webcam)
2. Pink object detection (gloves or any pink objects)
3. Virtual controller output (vJoy device)

Controls:
- 'q' or ESC: Quit
- 'c': Switch camera source
- 'r': Reset controller to neutral
- 'p': Recalibrate pink color detection
- 's': Save current frame
- 'h': Show help
"""

import cv2
import numpy as np
import pyvjoy
import threading
import time
import sys
from typing import Optional, Union, Tuple, List

class PinkGloveController:
    def __init__(self):
        # Camera system
        self.cap: Optional[cv2.VideoCapture] = None
        self.camera_sources = [
            {"name": "Default Camera (0)", "source": 0, "type": "webcam"},
            {"name": "Camera 1", "source": 1, "type": "webcam"},
            {"name": "Camera 2", "source": 2, "type": "webcam"},
            {"name": "IP Webcam (8080)", "source": "http://192.168.1.100:8080/video", "type": "ip"},
            {"name": "IP Webcam (4747)", "source": "http://192.168.1.100:4747/video", "type": "ip"},
        ]
        self.current_source_index = 0
        
        # Virtual controller
        self.vjoy_device = None
        self.controller_running = False
        
        # Controller state
        self.x_axis = 0      # -127 to 127 (Left brake)
        self.y_axis = 0      # -127 to 127 (Right brake)
        self.z_axis = 0      # -127 to 127 (Speed bar)
        self.x_rotation = 180  # 0 to 359 (Weight shift)
        self.buttons = [False] * 4
        
        # Pink detection parameters
        self.pink_lower = np.array([160, 50, 50])   # Lower HSV bound for pink
        self.pink_upper = np.array([180, 255, 255]) # Upper HSV bound for pink
        self.min_contour_area = 500  # Minimum area for detection
        
        # Hand tracking
        self.left_hand_pos = None
        self.right_hand_pos = None
        self.frame_center = (320, 240)  # Default center
        
        # Smoothing for stability
        self.smoothing_factor = 0.7
        self.last_x_axis = 0
        self.last_y_axis = 0
        self.last_z_axis = 0
        self.last_x_rotation = 180
        
        # Performance tracking
        self.frame_count = 0
        self.fps_counter = time.time()
        self.fps_display = 0.0
        
        # Initialize systems
        self.init_controller()
        self.init_camera()
        
    def init_controller(self):
        """Initialize vJoy virtual controller"""
        try:
            self.vjoy_device = pyvjoy.VJoyDevice(1)
            print("✅ vJoy device acquired successfully!")
            self.controller_running = True
            
            # Set initial neutral positions
            self.update_controller()
            
        except Exception as e:
            print(f"❌ Failed to initialize vJoy device: {e}")
            print("Please ensure vJoy driver is installed and configured!")
            sys.exit(1)
    
    def init_camera(self):
        """Initialize camera connection"""
        connected = False
        for i, source_info in enumerate(self.camera_sources):
            self.current_source_index = i
            if self.connect_camera(source_info['source']):
                connected = True
                break
        
        if not connected:
            print("❌ Could not connect to any camera source!")
            sys.exit(1)
    
    def connect_camera(self, source: Union[int, str]) -> bool:
        """Connect to camera source"""
        try:
            if self.cap:
                self.cap.release()
            
            print(f"Attempting to connect to: {source}")
            self.cap = cv2.VideoCapture(source)
            
            if isinstance(source, int):  # Webcam
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            ret, frame = self.cap.read()
            if ret:
                print(f"✅ Camera connected: {source}")
                self.frame_center = (frame.shape[1] // 2, frame.shape[0] // 2)
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Error connecting to camera {source}: {e}")
            return False
    
    def detect_pink_objects(self, frame: np.ndarray) -> List[Tuple[int, int, int]]:
        """Detect pink objects in frame and return their centers with areas"""
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create mask for pink color
        mask = cv2.inRange(hsv, self.pink_lower, self.pink_upper)
        
        # Clean up the mask with morphological operations
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find centers of significant pink objects
        pink_objects = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_contour_area:
                # Calculate center
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    pink_objects.append((cx, cy, int(area)))
        
        return pink_objects, mask
    
    def process_hand_positions(self, pink_objects: List[Tuple[int, int, int]]):
        """Process detected pink objects as hand positions"""
        if len(pink_objects) == 0:
            # No hands detected - gradually return to neutral
            self.left_hand_pos = None
            self.right_hand_pos = None
            return
        
        elif len(pink_objects) == 1:
            # One hand detected - determine if left or right based on position
            cx, cy, area = pink_objects[0]
            if cx < self.frame_center[0]:
                self.left_hand_pos = (cx, cy)
                self.right_hand_pos = None
            else:
                self.right_hand_pos = (cx, cy)
                self.left_hand_pos = None
        
        else:
            # Multiple objects - assign leftmost to left hand, rightmost to right hand
            pink_objects.sort(key=lambda x: x[0])  # Sort by x coordinate
            self.left_hand_pos = (pink_objects[0][0], pink_objects[0][1])
            self.right_hand_pos = (pink_objects[-1][0], pink_objects[-1][1])
    
    def calculate_controller_values(self):
        """Calculate controller axis values from hand positions"""
        frame_width, frame_height = self.frame_center[0] * 2, self.frame_center[1] * 2
        
        # Initialize with neutral values
        new_x_axis = 0    # Left brake
        new_y_axis = 0    # Right brake  
        new_z_axis = 0    # Speed bar
        new_x_rotation = 180  # Weight shift
        
        # Left hand controls X-axis (left brake)
        if self.left_hand_pos:
            # Map horizontal position to brake strength
            # Left side = more brake (positive), center = no brake (0)
            x_pos = self.left_hand_pos[0]
            # Map from 0-center to 0-127 (brake strength)
            new_x_axis = max(0, int((self.frame_center[0] - x_pos) * 127 / self.frame_center[0]))
        
        # Right hand controls Y-axis (right brake)
        if self.right_hand_pos:
            # Map horizontal position to brake strength
            # Right side = more brake (positive), center = no brake (0)
            x_pos = self.right_hand_pos[0]
            # Map from center-width to 0-127 (brake strength)
            new_y_axis = max(0, int((x_pos - self.frame_center[0]) * 127 / self.frame_center[0]))
        
        # Z-axis (speed bar) - average vertical position of both hands
        if self.left_hand_pos or self.right_hand_pos:
            y_positions = []
            if self.left_hand_pos:
                y_positions.append(self.left_hand_pos[1])
            if self.right_hand_pos:
                y_positions.append(self.right_hand_pos[1])
            
            avg_y = sum(y_positions) / len(y_positions)
            # Map vertical position to speed bar: top = pull (negative), bottom = push (positive)
            new_z_axis = int((avg_y - self.frame_center[1]) * 127 / self.frame_center[1])
            new_z_axis = max(-127, min(127, new_z_axis))
        
        # X-rotation (weight shift) - horizontal distance between hands
        if self.left_hand_pos and self.right_hand_pos:
            # Calculate weight shift based on relative positions
            left_x = self.left_hand_pos[0]
            right_x = self.right_hand_pos[0]
            center_of_hands = (left_x + right_x) / 2
            
            # Map to 0-359 degrees based on center of hands position
            shift_ratio = (center_of_hands - self.frame_center[0]) / self.frame_center[0]
            new_x_rotation = int(180 + shift_ratio * 90)  # 90-270 degree range
            new_x_rotation = max(0, min(359, new_x_rotation))
        
        # Apply smoothing to reduce jitter
        self.x_axis = int(self.smoothing_factor * self.last_x_axis + (1 - self.smoothing_factor) * new_x_axis)
        self.y_axis = int(self.smoothing_factor * self.last_y_axis + (1 - self.smoothing_factor) * new_y_axis)
        self.z_axis = int(self.smoothing_factor * self.last_z_axis + (1 - self.smoothing_factor) * new_z_axis)
        self.x_rotation = int(self.smoothing_factor * self.last_x_rotation + (1 - self.smoothing_factor) * new_x_rotation)
        
        # Store for next frame
        self.last_x_axis = self.x_axis
        self.last_y_axis = self.y_axis
        self.last_z_axis = self.z_axis
        self.last_x_rotation = self.x_rotation
    
    def update_controller(self):
        """Update the virtual controller with current values"""
        if not self.vjoy_device or not self.controller_running:
            return
        
        try:
            # Map to vJoy range (1-32768 with 16384 as center)
            vjoy_x = max(1, min(32768, int(16384 + (self.x_axis * 16384 / 127))))
            vjoy_y = max(1, min(32768, int(16384 + (self.y_axis * 16384 / 127))))
            vjoy_z = max(1, min(32768, int(16384 + (self.z_axis * 16384 / 127))))
            vjoy_rx = max(1, min(32768, int(1 + (self.x_rotation * 32767 / 359))))
            
            # Set axes
            self.vjoy_device.set_axis(pyvjoy.HID_USAGE_X, vjoy_x)
            self.vjoy_device.set_axis(pyvjoy.HID_USAGE_Y, vjoy_y)
            self.vjoy_device.set_axis(pyvjoy.HID_USAGE_Z, vjoy_z)
            self.vjoy_device.set_axis(pyvjoy.HID_USAGE_RX, vjoy_rx)
            
        except Exception as e:
            print(f"Error updating controller: {e}")
    
    def draw_overlay(self, frame: np.ndarray, pink_objects: List[Tuple[int, int, int]], mask: np.ndarray) -> np.ndarray:
        """Draw detection overlay on frame"""
        overlay = frame.copy()
        
        # Draw detected pink objects
        for i, (cx, cy, area) in enumerate(pink_objects):
            color = (0, 255, 0) if i < 2 else (0, 255, 255)  # Green for first two, yellow for others
            cv2.circle(overlay, (cx, cy), 20, color, 3)
            cv2.putText(overlay, f"Area: {area}", (cx-40, cy-30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Draw hand position indicators
        if self.left_hand_pos:
            cv2.circle(overlay, self.left_hand_pos, 30, (255, 0, 0), 3)  # Blue circle
            cv2.putText(overlay, "LEFT", (self.left_hand_pos[0]-20, self.left_hand_pos[1]-40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        if self.right_hand_pos:
            cv2.circle(overlay, self.right_hand_pos, 30, (0, 0, 255), 3)  # Red circle
            cv2.putText(overlay, "RIGHT", (self.right_hand_pos[0]-25, self.right_hand_pos[1]-40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Draw center reference lines
        cv2.line(overlay, (self.frame_center[0], 0), (self.frame_center[0], frame.shape[0]), (128, 128, 128), 1)
        cv2.line(overlay, (0, self.frame_center[1]), (frame.shape[1], self.frame_center[1]), (128, 128, 128), 1)
        
        # Draw controller values
        info_y = 30
        cv2.putText(overlay, f"Left Brake (X): {self.x_axis}", (10, info_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(overlay, f"Right Brake (Y): {self.y_axis}", (10, info_y + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(overlay, f"Speed Bar (Z): {self.z_axis}", (10, info_y + 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(overlay, f"Weight Shift (RX): {self.x_rotation}°", (10, info_y + 75), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw FPS
        cv2.putText(overlay, f"FPS: {self.fps_display:.1f}", (10, frame.shape[0] - 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw instructions
        cv2.putText(overlay, "Press 'h' for help", (10, frame.shape[0] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return overlay
    
    def calculate_fps(self) -> float:
        """Calculate current FPS"""
        current_time = time.time()
        elapsed = current_time - self.fps_counter
        if elapsed >= 1.0:
            fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_counter = current_time
            return fps
        return 0.0
    
    def show_instructions(self):
        """Show usage instructions"""
        print("\n" + "="*60)
        print("Pink Glove Controller - Controls:")
        print("="*60)
        print("'q' or ESC  - Quit")
        print("'c'         - Switch camera source")
        print("'r'         - Reset controller to neutral")
        print("'p'         - Recalibrate pink color detection")
        print("'s'         - Save current frame")
        print("'h'         - Show this help")
        print("\n" + "="*60)
        print("Hand Mapping:")
        print("- Left hand position  → Left brake (X-axis)")
        print("- Right hand position → Right brake (Y-axis)")
        print("- Vertical position   → Speed bar (Z-axis)")
        print("- Hands center        → Weight shift (X-rotation)")
        print("="*60)
    
    def reset_controller(self):
        """Reset controller to neutral position"""
        self.x_axis = 0
        self.y_axis = 0
        self.z_axis = 0
        self.x_rotation = 180
        self.last_x_axis = 0
        self.last_y_axis = 0
        self.last_z_axis = 0
        self.last_x_rotation = 180
        self.update_controller()
        print("Controller reset to neutral")
    
    def switch_camera(self) -> bool:
        """Switch to next camera source"""
        self.current_source_index = (self.current_source_index + 1) % len(self.camera_sources)
        source_info = self.camera_sources[self.current_source_index]
        print(f"Switching to: {source_info['name']}")
        return self.connect_camera(source_info['source'])
    
    def run(self):
        """Main application loop"""
        print("🎮 Pink Glove Controller Starting...")
        print("Put on pink gloves or hold pink objects!")
        self.show_instructions()
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Lost camera connection")
                    break
                
                self.frame_count += 1
                
                # Detect pink objects
                pink_objects, mask = self.detect_pink_objects(frame)
                
                # Process hand positions
                self.process_hand_positions(pink_objects)
                
                # Calculate controller values
                self.calculate_controller_values()
                
                # Update virtual controller
                self.update_controller()
                
                # Calculate FPS
                current_fps = self.calculate_fps()
                if current_fps > 0:
                    self.fps_display = current_fps
                
                # Draw overlay
                display_frame = self.draw_overlay(frame, pink_objects, mask)
                
                # Show frame
                cv2.imshow('Pink Glove Controller', display_frame)
                
                # Show mask in separate window (for debugging)
                cv2.imshow('Pink Detection Mask', mask)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or key == 27:  # 'q' or ESC
                    break
                elif key == ord('c'):  # Switch camera
                    if not self.switch_camera():
                        print("Failed to switch camera")
                elif key == ord('r'):  # Reset controller
                    self.reset_controller()
                elif key == ord('s'):  # Save frame
                    filename = f"pink_glove_frame_{int(time.time())}.jpg"
                    cv2.imwrite(filename, display_frame)
                    print(f"📸 Frame saved as: {filename}")
                elif key == ord('h'):  # Show help
                    self.show_instructions()
                elif key == ord('p'):  # Recalibrate pink detection (placeholder)
                    print("Pink recalibration feature - coming soon!")
                    
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up...")
        self.controller_running = False
        
        # Reset controller to neutral
        if self.vjoy_device:
            try:
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_X, 16384)
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_Y, 16384)
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_Z, 16384)
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_RX, 16384)
                for i in range(4):
                    self.vjoy_device.set_button(i + 1, False)
            except:
                pass
        
        # Release camera
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
        print("Pink Glove Controller ended.")

if __name__ == "__main__":
    try:
        controller = PinkGloveController()
        controller.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        input("Press Enter to exit...") 