import cv2
import numpy as np
import mediapipe as mp
import pyvjoy
import time
import sys
from typing import Optional, Union, Tuple, List, Dict

class HandTrackingController:
    def __init__(self):
        # Camera system
        self.cap: Optional[cv2.VideoCapture] = None
        self.camera_sources = [
            {"name": "Default Camera (0)", "source": 0, "type": "webcam"},
            {"name": "Camera 1", "source": 1, "type": "webcam"},
            {"name": "IP Webcam (8080)", "source": "http://192.168.1.100:8080/video", "type": "ip"},
        ]
        self.current_source_index = 0
        
        # MediaPipe setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Virtual controller
        self.vjoy_device = None
        
        # Controller state
        self.x_axis = 0      # -127 to 127 (Left brake)
        self.y_axis = 0      # -127 to 127 (Right brake)
        self.z_axis = 0      # -127 to 127 (Speed bar)
        self.x_rotation = 180  # 0 to 359 (Weight shift)
        self.buttons = [False] * 4
        
        # Hand tracking
        self.left_hand_landmarks = None
        self.right_hand_landmarks = None
        self.left_hand_pos = None
        self.right_hand_pos = None
        self.frame_center = (320, 240)
        
        # Gesture detection
        self.gesture_detection = True
        self.last_gestures = {"Left": "Open", "Right": "Open"}
        
        # Smoothing for stability
        self.smoothing_factor = 0.8
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
            self.update_controller()
        except Exception as e:
            print(f"❌ Failed to initialize vJoy device: {e}")
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
            
            ret, frame = self.cap.read()
            if ret:
                print(f"✅ Camera connected: {source}")
                self.frame_center = (frame.shape[1] // 2, frame.shape[0] // 2)
                return True
            return False
                
        except Exception as e:
            print(f"❌ Error connecting to camera {source}: {e}")
            return False
    
    def detect_hands(self, frame: np.ndarray):
        """Detect hands using MediaPipe"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.hands.process(rgb_frame)
        
        # Reset hand positions
        self.left_hand_landmarks = None
        self.right_hand_landmarks = None
        self.left_hand_pos = None
        self.right_hand_pos = None
        
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Get hand label (Left or Right)
                hand_label = handedness.classification[0].label
                
                # Get landmark coordinates
                h, w, _ = frame.shape
                landmarks = []
                for landmark in hand_landmarks.landmark:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    landmarks.append((x, y))
                
                # Calculate hand center (average of all landmarks)
                if landmarks:
                    center_x = int(sum(x for x, y in landmarks) / len(landmarks))
                    center_y = int(sum(y for x, y in landmarks) / len(landmarks))
                    
                    if hand_label == "Left":
                        self.left_hand_landmarks = landmarks
                        self.left_hand_pos = (center_x, center_y)
                    else:  # Right
                        self.right_hand_landmarks = landmarks
                        self.right_hand_pos = (center_x, center_y)
        
        return results
    
    def detect_gesture(self, landmarks: List[Tuple[int, int]]) -> str:
        """Detect simple hand gestures from landmarks"""
        if not landmarks or len(landmarks) < 21:
            return "Unknown"
        
        # MediaPipe hand landmark indices
        THUMB_TIP = 4
        THUMB_IP = 3
        INDEX_TIP = 8
        INDEX_PIP = 6
        MIDDLE_TIP = 12
        MIDDLE_PIP = 10
        RING_TIP = 16
        RING_PIP = 14
        PINKY_TIP = 20
        PINKY_PIP = 18
        
        # Check if fingers are extended
        fingers_up = []
        
        # Thumb (check x-coordinate relative to previous joint)
        if landmarks[THUMB_TIP][0] > landmarks[THUMB_IP][0]:  # Right hand logic
            fingers_up.append(1)
        else:
            fingers_up.append(0)
        
        # Other fingers (check y-coordinate)
        finger_tips = [INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
        finger_pips = [INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP]
        
        for tip, pip in zip(finger_tips, finger_pips):
            if landmarks[tip][1] < landmarks[pip][1]:  # Tip above PIP = finger up
                fingers_up.append(1)
            else:
                fingers_up.append(0)
        
        # Gesture recognition
        fingers_count = sum(fingers_up)
        
        if fingers_count == 0:
            return "Fist"
        elif fingers_count == 1 and fingers_up[1] == 1:  # Only index finger
            return "Point"
        elif fingers_count == 2 and fingers_up[1] == 1 and fingers_up[2] == 1:  # Index + Middle
            return "Peace"
        elif fingers_count == 5:
            return "Open"
        elif fingers_up[0] == 1 and sum(fingers_up[1:]) == 0:  # Only thumb
            return "Thumb"
        else:
            return "Other"
    
    def calculate_controller_values(self):
        """Calculate controller values from hand positions"""
        # Initialize with neutral values
        new_x_axis = 0
        new_y_axis = 0
        new_z_axis = 0
        new_x_rotation = 180
        
        # Left hand controls left brake (X-axis)
        if self.left_hand_pos:
            # Map horizontal position: left edge = max brake, center = no brake
            x_pos = self.left_hand_pos[0]
            distance_from_center = self.frame_center[0] - x_pos
            new_x_axis = max(0, min(127, int(distance_from_center * 127 / self.frame_center[0])))
        
        # Right hand controls right brake (Y-axis)
        if self.right_hand_pos:
            # Map horizontal position: right edge = max brake, center = no brake
            x_pos = self.right_hand_pos[0]
            distance_from_center = x_pos - self.frame_center[0]
            new_y_axis = max(0, min(127, int(distance_from_center * 127 / self.frame_center[0])))
        
        # Vertical position controls speed bar (Z-axis)
        if self.left_hand_pos or self.right_hand_pos:
            y_positions = []
            if self.left_hand_pos:
                y_positions.append(self.left_hand_pos[1])
            if self.right_hand_pos:
                y_positions.append(self.right_hand_pos[1])
            
            avg_y = sum(y_positions) / len(y_positions)
            # Map vertical: top = pull (negative), bottom = push (positive)
            new_z_axis = int((avg_y - self.frame_center[1]) * 127 / self.frame_center[1])
            new_z_axis = max(-127, min(127, new_z_axis))
        
        # Weight shift based on center of hands
        if self.left_hand_pos and self.right_hand_pos:
            center_x = (self.left_hand_pos[0] + self.right_hand_pos[0]) / 2
            shift = (center_x - self.frame_center[0]) / self.frame_center[0]
            new_x_rotation = int(180 + shift * 90)
            new_x_rotation = max(0, min(359, new_x_rotation))
        
        # Apply smoothing
        self.x_axis = int(self.smoothing_factor * self.last_x_axis + (1 - self.smoothing_factor) * new_x_axis)
        self.y_axis = int(self.smoothing_factor * self.last_y_axis + (1 - self.smoothing_factor) * new_y_axis)
        self.z_axis = int(self.smoothing_factor * self.last_z_axis + (1 - self.smoothing_factor) * new_z_axis)
        self.x_rotation = int(self.smoothing_factor * self.last_x_rotation + (1 - self.smoothing_factor) * new_x_rotation)
        
        # Update gesture-based buttons
        if self.gesture_detection:
            self.update_gesture_buttons()
        
        # Store for next frame
        self.last_x_axis = self.x_axis
        self.last_y_axis = self.y_axis
        self.last_z_axis = self.z_axis
        self.last_x_rotation = self.x_rotation
    
    def update_gesture_buttons(self):
        """Update button states based on detected gestures"""
        # Reset buttons
        self.buttons = [False] * 4
        
        # Map gestures to buttons
        gesture_map = {
            "Fist": 0,
            "Point": 1, 
            "Peace": 2,
            "Thumb": 3
        }
        
        # Check left hand gesture
        if self.left_hand_landmarks:
            left_gesture = self.detect_gesture(self.left_hand_landmarks)
            if left_gesture in gesture_map:
                self.buttons[gesture_map[left_gesture]] = True
            self.last_gestures["Left"] = left_gesture
        
        # Check right hand gesture  
        if self.right_hand_landmarks:
            right_gesture = self.detect_gesture(self.right_hand_landmarks)
            if right_gesture in gesture_map:
                button_idx = gesture_map[right_gesture]
                # Use different buttons for right hand to avoid conflicts
                if button_idx < 2:  # Map to buttons 2,3 for right hand
                    self.buttons[button_idx + 2] = True
            self.last_gestures["Right"] = right_gesture
    
    def update_controller(self):
        """Update the virtual controller"""
        if not self.vjoy_device:
            return
        
        try:
            # Map to vJoy range
            vjoy_x = max(1, min(32768, int(16384 + (self.x_axis * 16384 / 127))))
            vjoy_y = max(1, min(32768, int(16384 + (self.y_axis * 16384 / 127))))
            vjoy_z = max(1, min(32768, int(16384 + (self.z_axis * 16384 / 127))))
            vjoy_rx = max(1, min(32768, int(1 + (self.x_rotation * 32767 / 359))))
            
            self.vjoy_device.set_axis(pyvjoy.HID_USAGE_X, vjoy_x)
            self.vjoy_device.set_axis(pyvjoy.HID_USAGE_Y, vjoy_y)
            self.vjoy_device.set_axis(pyvjoy.HID_USAGE_Z, vjoy_z)
            self.vjoy_device.set_axis(pyvjoy.HID_USAGE_RX, vjoy_rx)
            
            # Set buttons
            for i, pressed in enumerate(self.buttons):
                self.vjoy_device.set_button(i + 1, pressed)
            
        except Exception as e:
            print(f"Error updating controller: {e}")
    
    def draw_overlay(self, frame, results):
        """Draw hand tracking overlay"""
        overlay = frame.copy()
        
        # Draw hand landmarks
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                hand_label = handedness.classification[0].label
                
                # Draw landmarks
                self.mp_draw.draw_landmarks(overlay, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # Draw hand label and center
                if hand_label == "Left" and self.left_hand_pos:
                    cv2.circle(overlay, self.left_hand_pos, 15, (255, 0, 0), 3)
                    cv2.putText(overlay, f"LEFT - {self.last_gestures['Left']}", 
                               (self.left_hand_pos[0]-40, self.left_hand_pos[1]-30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                elif hand_label == "Right" and self.right_hand_pos:
                    cv2.circle(overlay, self.right_hand_pos, 15, (0, 0, 255), 3)
                    cv2.putText(overlay, f"RIGHT - {self.last_gestures['Right']}", 
                               (self.right_hand_pos[0]-40, self.right_hand_pos[1]-30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Draw center lines
        cv2.line(overlay, (self.frame_center[0], 0), (self.frame_center[0], frame.shape[0]), (128, 128, 128), 1)
        cv2.line(overlay, (0, self.frame_center[1]), (frame.shape[1], self.frame_center[1]), (128, 128, 128), 1)
        
        # Draw controller values
        y_offset = 30
        cv2.putText(overlay, f"Left Brake: {self.x_axis}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(overlay, f"Right Brake: {self.y_axis}", (10, y_offset + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(overlay, f"Speed Bar: {self.z_axis}", (10, y_offset + 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(overlay, f"Weight Shift: {self.x_rotation}°", (10, y_offset + 75), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw button states
        button_text = f"Buttons: {[i+1 for i, pressed in enumerate(self.buttons) if pressed]}"
        cv2.putText(overlay, button_text, (10, y_offset + 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Draw FPS and gesture status
        cv2.putText(overlay, f"FPS: {self.fps_display:.1f}", (10, frame.shape[0] - 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        gesture_status = "ON" if self.gesture_detection else "OFF"
        cv2.putText(overlay, f"Gestures: {gesture_status}", (10, frame.shape[0] - 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(overlay, "Press 'h' for help", (10, frame.shape[0] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return overlay
    
    def calculate_fps(self):
        """Calculate FPS"""
        current_time = time.time()
        elapsed = current_time - self.fps_counter
        if elapsed >= 1.0:
            fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_counter = current_time
            return fps
        return 0.0
    
    def show_help(self):
        """Show help message"""
        print("\n" + "="*60)
        print("Hand Tracking Controller - Instructions:")
        print("="*60)
        print("No gloves needed! Just use your bare hands.")
        print("\nHand Controls:")
        print("- Left hand position  → Left brake")
        print("- Right hand position → Right brake")
        print("- Vertical position   → Speed bar")
        print("- Center of hands     → Weight shift")
        print("\nGestures (when enabled):")
        print("- Fist     → Button 1")
        print("- Point    → Button 2") 
        print("- Peace    → Button 3")
        print("- Thumbs Up → Button 4")
        print("\nKeys:")
        print("'q' - Quit, 'c' - Switch camera")
        print("'r' - Reset, 's' - Save frame")
        print("'g' - Toggle gestures, 'h' - Help")
        print("="*60)
    
    def run(self):
        """Main loop"""
        print("👋 Hand Tracking Controller Starting...")
        print("No gloves needed - just wave your hands!")
        self.show_help()
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                self.frame_count += 1
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Detect hands
                results = self.detect_hands(frame)
                
                # Calculate controller values
                self.calculate_controller_values()
                
                # Update controller
                self.update_controller()
                
                # Calculate FPS
                fps = self.calculate_fps()
                if fps > 0:
                    self.fps_display = fps
                
                # Draw overlay
                display_frame = self.draw_overlay(frame, results)
                
                # Show frame
                cv2.imshow('Hand Tracking Controller', display_frame)
                
                # Handle keys
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break
                elif key == ord('c'):
                    print("Camera switching - feature coming soon!")
                elif key == ord('r'):
                    # Reset controller
                    self.x_axis = 0
                    self.y_axis = 0
                    self.z_axis = 0
                    self.x_rotation = 180
                    self.buttons = [False] * 4
                    print("Controller reset to neutral")
                elif key == ord('g'):
                    # Toggle gesture detection
                    self.gesture_detection = not self.gesture_detection
                    status = "enabled" if self.gesture_detection else "disabled"
                    print(f"Gesture detection {status}")
                elif key == ord('s'):
                    # Save frame
                    filename = f"hand_tracking_{int(time.time())}.jpg"
                    cv2.imwrite(filename, display_frame)
                    print(f"Saved {filename}")
                elif key == ord('h'):
                    self.show_help()
                    
        except KeyboardInterrupt:
            print("\nStopped by user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        print("Cleaning up...")
        if self.vjoy_device:
            try:
                # Reset to neutral
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_X, 16384)
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_Y, 16384)
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_Z, 16384)
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_RX, 16384)
                for i in range(4):
                    self.vjoy_device.set_button(i + 1, False)
            except:
                pass
        
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        controller = HandTrackingController()
        controller.run()
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")
