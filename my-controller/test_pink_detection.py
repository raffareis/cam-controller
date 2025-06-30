"""
Pink Detection Test - Quick test for pink object detection

This simple script helps you test if your pink objects are being detected properly
before running the full pink glove controller.

Controls:
- 'q' or ESC: Quit
- 's': Save frame
- '+'/'-': Adjust detection sensitivity
"""

import cv2
import numpy as np
import time

def test_pink_detection():
    # Pink detection parameters (HSV)
    pink_lower = np.array([160, 50, 50])   # Lower bound
    pink_upper = np.array([180, 255, 255]) # Upper bound
    min_area = 500  # Minimum area for detection
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open camera")
        return
    
    print("🌸 Pink Detection Test")
    print("Put on pink gloves or hold pink objects in front of camera")
    print("Press '+' to increase sensitivity, '-' to decrease")
    print("Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create pink mask
        mask = cv2.inRange(hsv, pink_lower, pink_upper)
        
        # Clean up mask
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw detection results
        result = frame.copy()
        detected_count = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                detected_count += 1
                # Draw bounding box
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Draw center
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    cv2.circle(result, (cx, cy), 10, (0, 255, 0), -1)
                    cv2.putText(result, f"Area: {int(area)}", (cx-40, cy-20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Add info overlay
        cv2.putText(result, f"Pink objects detected: {detected_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(result, f"Pink range: {pink_lower} - {pink_upper}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(result, f"Min area: {min_area}", (10, 85), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Status indicator
        status_color = (0, 255, 0) if detected_count >= 1 else (0, 0, 255)
        status_text = "GOOD" if detected_count >= 1 else "NO DETECTION"
        cv2.putText(result, status_text, (10, result.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        
        # Show images
        cv2.imshow('Pink Detection Test', result)
        cv2.imshow('Pink Mask', mask)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('+') or key == ord('='):
            # Increase sensitivity (expand range)
            pink_lower[1] = max(0, pink_lower[1] - 10)    # Lower saturation
            pink_lower[2] = max(0, pink_lower[2] - 10)    # Lower value
            print(f"Increased sensitivity: {pink_lower} - {pink_upper}")
        elif key == ord('-'):
            # Decrease sensitivity (narrow range)
            pink_lower[1] = min(255, pink_lower[1] + 10)  # Higher saturation
            pink_lower[2] = min(255, pink_lower[2] + 10)  # Higher value
            print(f"Decreased sensitivity: {pink_lower} - {pink_upper}")
        elif key == ord('s'):
            # Save frame
            filename = f"pink_test_{int(time.time())}.jpg"
            cv2.imwrite(filename, result)
            print(f"Saved {filename}")
    
    cap.release()
    cv2.destroyAllWindows()
    print("Pink detection test ended")

if __name__ == "__main__":
    try:
        test_pink_detection()
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...") 