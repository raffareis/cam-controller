"""
Hand Detection Test - Quick test for MediaPipe hand tracking

This simple script tests MediaPipe hand detection to verify it's working
before running the full hand tracking controller.

Controls:
- 'q' or ESC: Quit
- 's': Save frame
- 'g': Toggle gesture labels
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import python
import time

def test_hand_detection():
    # MediaPipe setup
    mp_hands = mp.solutions.hands
    
    base_options = python.BaseOptions(model_asset_path='pose_landmarker.task')
    hands = mp_hands.Hands(  
        base_options = base_options,
        static_image_mode=False,    
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    mp_draw = mp.solutions.drawing_utils
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open camera")
        return
    
    print("👋 Hand Detection Test")
    print("Show your hands to the camera - no gloves needed!")
    print("Press 'g' to toggle gesture labels, 'q' to quit")
    
    show_gestures = True
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Flip frame for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = hands.process(rgb_frame)
        
        # Draw results
        hand_count = 0
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                hand_count += 1
                hand_label = handedness.classification[0].label
                
                # Draw landmarks
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # Calculate hand center
                h, w, _ = frame.shape
                landmarks = []
                for landmark in hand_landmarks.landmark:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    landmarks.append((x, y))
                
                if landmarks:
                    center_x = int(sum(x for x, y in landmarks) / len(landmarks))
                    center_y = int(sum(y for x, y in landmarks) / len(landmarks))
                    
                    # Draw hand center and label
                    color = (255, 0, 0) if hand_label == "Left" else (0, 0, 255)
                    cv2.circle(frame, (center_x, center_y), 10, color, -1)
                    
                    # Detect simple gesture
                    gesture = "Unknown"
                    if show_gestures and len(landmarks) >= 21:
                        gesture = detect_simple_gesture(landmarks)
                    
                    cv2.putText(frame, f"{hand_label} - {gesture}", 
                               (center_x-40, center_y-30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Add info overlay
        cv2.putText(frame, f"Hands detected: {hand_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Gestures: {'ON' if show_gestures else 'OFF'}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Status indicator
        status_color = (0, 255, 0) if hand_count >= 1 else (0, 0, 255)
        status_text = "TRACKING" if hand_count >= 1 else "NO HANDS"
        cv2.putText(frame, status_text, (10, frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        
        # Show frame
        cv2.imshow('Hand Detection Test', frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('g'):
            show_gestures = not show_gestures
            print(f"Gesture labels: {'enabled' if show_gestures else 'disabled'}")
        elif key == ord('s'):
            # Save frame
            filename = f"hand_test_{int(time.time())}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Saved {filename}")
    
    cap.release()
    cv2.destroyAllWindows()
    print("Hand detection test ended")

def detect_simple_gesture(landmarks):
    """Detect simple gestures from landmarks"""
    if len(landmarks) < 21:
        return "Unknown"
    
    # Landmark indices
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
    
    # Thumb
    if landmarks[THUMB_TIP][0] > landmarks[THUMB_IP][0]:
        fingers_up.append(1)
    else:
        fingers_up.append(0)
    
    # Other fingers
    finger_tips = [INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
    finger_pips = [INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP]
    
    for tip, pip in zip(finger_tips, finger_pips):
        if landmarks[tip][1] < landmarks[pip][1]:  # Tip above PIP
            fingers_up.append(1)
        else:
            fingers_up.append(0)
    
    # Gesture recognition
    fingers_count = sum(fingers_up)
    
    if fingers_count == 0:
        return "Fist"
    elif fingers_count == 1 and fingers_up[1] == 1:
        return "Point"
    elif fingers_count == 2 and fingers_up[1] == 1 and fingers_up[2] == 1:
        return "Peace"
    elif fingers_count == 5:
        return "Open"
    elif fingers_up[0] == 1 and sum(fingers_up[1:]) == 0:
        return "Thumbs Up"
    else:
        return f"{fingers_count} fingers"

if __name__ == "__main__":
    try:
        test_hand_detection()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure MediaPipe is installed: pip install mediapipe")
        input("Press Enter to exit...") 