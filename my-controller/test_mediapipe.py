import time
import threading
import math
import collections
from enum import Enum, auto
from types import SimpleNamespace
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import cv2
import pyvjoy
import sys

# Locks and result holders for asynchronous processing
pose_lock = threading.Lock()
latest_pose_result = None
gesture_lock = threading.Lock()
latest_gesture_result = None

VJOY_MAX_RANGE = 32768
VJOY_CENTER = VJOY_MAX_RANGE // 2

def map_to_vjoy_axis(value_minus_1_to_1):
    """Maps a value from -1.0..1.0 to vJoy's 1..32768 range."""
    vjoy_value = int(VJOY_CENTER + value_minus_1_to_1 * (VJOY_CENTER - 1))
    return max(1, min(VJOY_MAX_RANGE, vjoy_value))

class HandState(Enum):
    TRACKING = auto()
    RELEASED = auto()

left_hand_status = HandState.TRACKING
right_hand_status = HandState.TRACKING

# Gesture debounce/streak variables
GESTURE_STREAK_REQUIRED = 3
left_gesture_streak = 0
right_gesture_streak = 0
left_last_seen_gesture = None
right_last_seen_gesture = None

# New calibration state machine
class CalibrationStatus(Enum):
    NOT_CALIBRATED = "Show two open hands to begin calibration"
    ARMING = "Hold pose for 0.5 seconds..."
    READY_TO_SET = "Close both hands to set position"
    CALIBRATED = "Calibrated! Show open hands to re-calibrate."

calibration_status = CalibrationStatus.NOT_CALIBRATED
arming_start_time = None
pose_data_buffer = collections.deque(maxlen=5)

# Calibration and state variables
is_calibrated = False
initial_state = {}
CALIBRATION_THRESHOLD = 0.15 # Distance in meters between thumb and pinky to detect an open hand
calibration_message = "Show two open hands to calibrate..."

def get_color_for_distance(distance, max_distance=0.5):
    """Interpolates color from green to red based on distance."""
    # Clamp the distance to the max_distance
    distance = min(distance, max_distance)
    ratio = distance / max_distance
    # BGR color format for OpenCV
    # As ratio goes from 0 to 1, green goes from 255 to 0, and red goes from 0 to 255.
    green = int(255 * (1 - ratio))
    red = int(255 * ratio)
    return (0, green, red)

def calculate_torso_angle(landmarks):
    """Calculates the torso angle based on a vector from hip-center to shoulder-center."""
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    left_hip = landmarks[23]
    right_hip = landmarks[24]

    # Calculate midpoints
    shoulder_midpoint_x = (left_shoulder.x + right_shoulder.x) / 2
    shoulder_midpoint_y = (left_shoulder.y + right_shoulder.y) / 2
    
    hip_midpoint_x = (left_hip.x + right_hip.x) / 2
    hip_midpoint_y = (left_hip.y + right_hip.y) / 2
    
    # Vector from hips to shoulders
    dx = shoulder_midpoint_x - hip_midpoint_x
    dy = shoulder_midpoint_y - hip_midpoint_y
    
    # Calculate angle with respect to the absolute vertical UP axis.
    # math.atan2(y, x) calculates angle from the positive X axis.
    # Vertical UP in MediaPipe's coordinates is along the negative Y axis.
    # This corresponds to an angle of -pi/2 or 270 degrees. We add pi/2 to make UP = 0 rad.
    angle_rad = math.atan2(dy, dx) + (math.pi / 2)
    
    # Normalize the angle to be within [-pi, pi]
    if angle_rad > math.pi:
        angle_rad -= 2 * math.pi
        
    return angle_rad

def average_initial_state(buffer):
    """Averages the last few pose data points to get a stable initial state."""
    if not buffer or len(buffer) < 1:
        return None

    # Initialize accumulators
    avg_l_hand_3d, avg_r_hand_3d, avg_head_3d = np.zeros(3), np.zeros(3), np.zeros(3)
    avg_l_hand_2d, avg_r_hand_2d, avg_head_2d = np.zeros(2), np.zeros(2), np.zeros(2)
    torso_angles = []

    for res in buffer:
        landmarks_3d = res.pose_world_landmarks[0]
        landmarks_2d = res.pose_landmarks[0]
        
        avg_l_hand_3d += [landmarks_3d[15].x, landmarks_3d[15].y, landmarks_3d[15].z]
        avg_r_hand_3d += [landmarks_3d[16].x, landmarks_3d[16].y, landmarks_3d[16].z]
        avg_head_3d += [landmarks_3d[0].x, landmarks_3d[0].y, landmarks_3d[0].z]
        
        avg_l_hand_2d += [landmarks_2d[15].x, landmarks_2d[15].y]
        avg_r_hand_2d += [landmarks_2d[16].x, landmarks_2d[16].y]
        avg_head_2d += [landmarks_2d[0].x, landmarks_2d[0].y]

        torso_angles.append(calculate_torso_angle(landmarks_3d))

    num_samples = len(buffer)
    avg_l_hand_3d /= num_samples
    avg_r_hand_3d /= num_samples
    avg_head_3d /= num_samples
    avg_l_hand_2d /= num_samples
    avg_r_hand_2d /= num_samples
    avg_head_2d /= num_samples
    
    avg_state = {
        'left_hand_pos': SimpleNamespace(x=avg_l_hand_3d[0], y=avg_l_hand_3d[1], z=avg_l_hand_3d[2]),
        'right_hand_pos': SimpleNamespace(x=avg_r_hand_3d[0], y=avg_r_hand_3d[1], z=avg_r_hand_3d[2]),
        'head_pos_3d': SimpleNamespace(x=avg_head_3d[0], y=avg_head_3d[1], z=avg_head_3d[2]),
        'left_hand_pos_2d': SimpleNamespace(x=avg_l_hand_2d[0], y=avg_l_hand_2d[1]),
        'right_hand_pos_2d': SimpleNamespace(x=avg_r_hand_2d[0], y=avg_r_hand_2d[1]),
        'head_pos_2d': SimpleNamespace(x=avg_head_2d[0], y=avg_head_2d[1]),
        'torso_angle': np.mean(torso_angles)
    }
    
    avg_state['left_hand_head_y_offset'] = avg_state['left_hand_pos'].y - avg_state['head_pos_3d'].y
    avg_state['right_hand_head_y_offset'] = avg_state['right_hand_pos'].y - avg_state['head_pos_3d'].y
    
    return avg_state

def get_hand_gestures(gestures, handedness):
    """Parses gesture results into a dictionary."""
    hand_gestures = {}
    if not gestures or not handedness:
        return hand_gestures
    
    for i in range(len(gestures)):
        hand = handedness[i][0].category_name
        gesture = gestures[i][0].category_name
        hand_gestures[hand] = gesture
            
    return hand_gestures

def draw_landmarks_on_image(rgb_image, detection_result):
  if not detection_result or not detection_result.pose_landmarks:
      return rgb_image

  pose_landmarks_list = detection_result.pose_landmarks
  annotated_image = np.copy(rgb_image)

  # Loop through the detected poses to visualize.
  for idx in range(len(pose_landmarks_list)):
    pose_landmarks = pose_landmarks_list[idx]

    # Draw the pose landmarks.
    pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
    pose_landmarks_proto.landmark.extend([
      landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in pose_landmarks
    ])
    solutions.drawing_utils.draw_landmarks(
      annotated_image,
      pose_landmarks_proto,
      solutions.pose.POSE_CONNECTIONS,
      solutions.drawing_styles.get_default_pose_landmarks_style())
  return annotated_image

def pose_result_callback(result: vision.PoseLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    """Callback function to receive pose detection results asynchronously."""
    global latest_pose_result
    with pose_lock:
        latest_pose_result = result

def gesture_result_callback(result: vision.GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
    """Callback function to receive gesture recognition results asynchronously."""
    global latest_gesture_result
    with gesture_lock:
        latest_gesture_result = result

if __name__ == "__main__":
    # STEP 1: Initialize vJoy
    try:
        vjoy_device = pyvjoy.VJoyDevice(1)
        print("vJoy device 1 acquired successfully!")
    except pyvjoy.vJoyException as e:
        print(f"vJoy Error: {e}", file=sys.stderr)
        print("Please ensure vJoy is installed, enabled, and device 1 is configured.", file=sys.stderr)
        sys.exit(1)

    # STEP 2: Create a PoseLandmarker object.
    pose_base_options = python.BaseOptions(model_asset_path='pose_landmarker.task', delegate='GPU')
    pose_options = vision.PoseLandmarkerOptions(
        base_options=pose_base_options,
        running_mode=vision.RunningMode.LIVE_STREAM,
        result_callback=pose_result_callback,
        output_segmentation_masks=True)

    # Create a GestureRecognizer object.
    gesture_base_options = python.BaseOptions(model_asset_path='gesture_recognizer.task', delegate='GPU')
    gesture_options = vision.GestureRecognizerOptions(
        base_options=gesture_base_options,
        running_mode=vision.RunningMode.LIVE_STREAM,
        result_callback=gesture_result_callback,
        num_hands=2)

    with vision.PoseLandmarker.create_from_options(pose_options) as pose_detector, \
         vision.GestureRecognizer.create_from_options(gesture_options) as gesture_recognizer:

        cap = cv2.VideoCapture(0)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert the BGR image to RGB.
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # Get current time in milliseconds
            timestamp_ms = int(time.time() * 1000)
            pose_detector.detect_async(mp_image, timestamp_ms)
            gesture_recognizer.recognize_async(mp_image, timestamp_ms)
            
            display_image = frame.copy() 
            with pose_lock, gesture_lock:
                if latest_pose_result and latest_pose_result.pose_world_landmarks:
                    # Always buffer pose data if a pose is detected
                    pose_data_buffer.append(latest_pose_result)

                    # --- CALIBRATION STATE MACHINE ---
                    gestures = latest_gesture_result.gestures if latest_gesture_result else None
                    handedness = latest_gesture_result.handedness if latest_gesture_result else None
                    current_gestures = get_hand_gestures(gestures, handedness)

                    if calibration_status == CalibrationStatus.NOT_CALIBRATED:
                        if current_gestures.get('Left') == 'Open_Palm' and current_gestures.get('Right') == 'Open_Palm':
                            calibration_status = CalibrationStatus.ARMING
                            arming_start_time = time.time()
                    
                    elif calibration_status == CalibrationStatus.ARMING:
                        if not (current_gestures.get('Left') == 'Open_Palm' and current_gestures.get('Right') == 'Open_Palm'):
                            # If arming fails, revert to previous state (calibrated or not)
                            calibration_status = CalibrationStatus.CALIBRATED if is_calibrated else CalibrationStatus.NOT_CALIBRATED
                            arming_start_time = None
                        elif time.time() - (arming_start_time or 0) >= 0.5:
                            calibration_status = CalibrationStatus.READY_TO_SET
                    
                    elif calibration_status == CalibrationStatus.READY_TO_SET:
                        if current_gestures.get('Left') == 'Closed_Fist' and current_gestures.get('Right') == 'Closed_Fist':
                            initial_state = average_initial_state(pose_data_buffer)
                            if initial_state:
                                is_calibrated = True
                                left_hand_status = HandState.TRACKING
                                right_hand_status = HandState.TRACKING
                                calibration_status = CalibrationStatus.CALIBRATED
                            else:
                                calibration_status = CalibrationStatus.NOT_CALIBRATED
                    
                    elif calibration_status == CalibrationStatus.CALIBRATED:
                        if current_gestures.get('Left') == 'Open_Palm' and current_gestures.get('Right') == 'Open_Palm':
                            # Begin re-calibration process, but keep tracking with old data
                            calibration_status = CalibrationStatus.ARMING
                            arming_start_time = time.time()

                    # Draw 2D landmarks from pose, regardless of calibration status
                    annotated_image = draw_landmarks_on_image(rgb_frame, latest_pose_result)
                    display_image = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
                    
                    if is_calibrated:
                        # --- INDIVIDUAL HAND STATE LOGIC with DEBOUNCE ---
                        landmarks_3d = latest_pose_result.pose_world_landmarks[0]
                        current_head_pos_3d = landmarks_3d[0]
                        
                        # Left Hand Debounce
                        current_left_gesture = current_gestures.get('Left')
                        if current_left_gesture == left_last_seen_gesture:
                            left_gesture_streak += 1
                        else:
                            left_last_seen_gesture = current_left_gesture
                            left_gesture_streak = 1
                            
                        if left_gesture_streak >= GESTURE_STREAK_REQUIRED:
                            if left_hand_status == HandState.TRACKING and left_last_seen_gesture == 'Open_Palm':
                                left_hand_status = HandState.RELEASED
                                left_gesture_streak = 0 # Reset streak to require a new one to change back
                            elif left_hand_status == HandState.RELEASED and left_last_seen_gesture == 'Closed_Fist':
                                left_hand_status = HandState.TRACKING
                                initial_state['left_hand_head_y_offset'] = landmarks_3d[15].y - current_head_pos_3d.y
                                left_gesture_streak = 0

                        # Right Hand Debounce
                        current_right_gesture = current_gestures.get('Right')
                        if current_right_gesture == right_last_seen_gesture:
                            right_gesture_streak += 1
                        else:
                            right_last_seen_gesture = current_right_gesture
                            right_gesture_streak = 1

                        if right_gesture_streak >= GESTURE_STREAK_REQUIRED:
                            if right_hand_status == HandState.TRACKING and right_last_seen_gesture == 'Open_Palm':
                                right_hand_status = HandState.RELEASED
                                right_gesture_streak = 0
                            elif right_hand_status == HandState.RELEASED and right_last_seen_gesture == 'Closed_Fist':
                                right_hand_status = HandState.TRACKING
                                initial_state['right_hand_head_y_offset'] = landmarks_3d[16].y - current_head_pos_3d.y
                                right_gesture_streak = 0

                        # --- TRACKING LOGIC ---
                        img_height, img_width, _ = display_image.shape
                        
                        # 1. Calculate relative hand positions
                        current_left_hand_pos = landmarks_3d[15]
                        rel_left = (
                            current_left_hand_pos.x - initial_state['left_hand_pos'].x,
                            current_left_hand_pos.y - initial_state['left_hand_pos'].y,
                            current_left_hand_pos.z - initial_state['left_hand_pos'].z,
                        )

                        current_right_hand_pos = landmarks_3d[16]
                        rel_right = (
                            current_right_hand_pos.x - initial_state['right_hand_pos'].x,
                            current_right_hand_pos.y - initial_state['right_hand_pos'].y,
                            current_right_hand_pos.z - initial_state['right_hand_pos'].z,
                        )

                        # 2. Calculate relative torso inclination
                        current_torso_angle = calculate_torso_angle(landmarks_3d)
                        rel_incline_rad = current_torso_angle - initial_state['torso_angle']
                        rel_incline_deg = np.rad2deg(rel_incline_rad)

                        # 3. Calculate vertical hand travel relative to head
                        left_vertical_travel = 0
                        if left_hand_status == HandState.TRACKING:
                            left_current_y_offset = current_left_hand_pos.y - current_head_pos_3d.y
                            left_vertical_travel = -(left_current_y_offset - initial_state['left_hand_head_y_offset'])

                        right_vertical_travel = 0
                        if right_hand_status == HandState.TRACKING:
                            right_current_y_offset = current_right_hand_pos.y - current_head_pos_3d.y
                            right_vertical_travel = -(right_current_y_offset - initial_state['right_hand_head_y_offset'])

                        # --- VJOY UPDATE LOGIC ---
                        MAX_TRAVEL_METERS = 0.4 # 40cm for full deflection
                        MAX_LEAN_DEGREES = 25   # degrees for full weight shift

                        # Calculate pull amount (0 to 1), only considering downward movement
                        left_pull = max(0, -left_vertical_travel)
                        right_pull = max(0, -right_vertical_travel)

                        # Normalize pull to [0, 1] range. This represents 0% to 100% brake.
                        norm_left_brake_0_to_1 = np.clip(left_pull / MAX_TRAVEL_METERS, 0.0, 1.0)
                        norm_right_brake_0_to_1 = np.clip(right_pull / MAX_TRAVEL_METERS, 0.0, 1.0)
                        
                        # Map the [0, 1] brake pull to the full joystick axis range [-1, 1]
                        # This gives the game maximum resolution. Neutral (0 pull) is -1. Full pull is 1.
                        norm_left_brake = (norm_left_brake_0_to_1 * 2.0) - 1.0
                        norm_right_brake = -((norm_right_brake_0_to_1 * 2.0) - 1.0) # Inverted for Y-axis

                        # Normalize lean to [-1, 1] range
                        norm_lean = np.clip(rel_incline_deg / MAX_LEAN_DEGREES, -1.0, 1.0)

                        # Map to vJoy axes. Left hand -> X, Right hand -> Y, Lean -> RX
                        vjoy_x = map_to_vjoy_axis(norm_left_brake)
                        vjoy_y = map_to_vjoy_axis(norm_right_brake)
                        vjoy_rx = map_to_vjoy_axis(norm_lean)
                        
                        vjoy_device.set_axis(pyvjoy.HID_USAGE_X, vjoy_x)
                        vjoy_device.set_axis(pyvjoy.HID_USAGE_Y, vjoy_y)
                        vjoy_device.set_axis(pyvjoy.HID_USAGE_RX, vjoy_rx)
                        
                        # Set other axes to neutral for now
                        vjoy_device.set_axis(pyvjoy.HID_USAGE_Z, VJOY_CENTER)

                        # --- DRAWING MOVEMENT VECTORS ON 2D IMAGE ---
                        if latest_pose_result.pose_landmarks:
                            landmarks_2d = latest_pose_result.pose_landmarks[0]

                            # Calculate 3D distances for color
                            dist_left_3d = math.hypot(*rel_left)
                            dist_right_3d = math.hypot(*rel_right)
                            
                            color_left = get_color_for_distance(dist_left_3d)
                            color_right = get_color_for_distance(dist_right_3d)

                            # Convert normalized 2D coords to pixel coords and draw lines
                            start_point_left = (int(initial_state['left_hand_pos_2d'].x * img_width), int(initial_state['left_hand_pos_2d'].y * img_height))
                            end_point_left = (int(landmarks_2d[15].x * img_width), int(landmarks_2d[15].y * img_height))
                            cv2.line(display_image, start_point_left, end_point_left, color_left, 3)

                            start_point_right = (int(initial_state['right_hand_pos_2d'].x * img_width), int(initial_state['right_hand_pos_2d'].y * img_height))
                            end_point_right = (int(landmarks_2d[16].x * img_width), int(landmarks_2d[16].y * img_height))
                            cv2.line(display_image, start_point_right, end_point_right, color_right, 3)

                        # --- DRAWING VERTICAL TRAVEL BARS ---
                        VERTICAL_SCALE_FACTOR = 800 # pixels per meter
                        
                        # Define bar positions and zero-line y-coordinate
                        left_bar_x = int(img_width * 0.1)
                        right_bar_x = int(img_width * 0.9)
                        zero_y = int(initial_state['head_pos_2d'].y * img_height)

                        # Draw zero-lines
                        cv2.line(display_image, (left_bar_x - 10, zero_y), (left_bar_x + 10, zero_y), (0, 0, 0), 2)
                        cv2.line(display_image, (right_bar_x - 10, zero_y), (right_bar_x + 10, zero_y), (0, 0, 0), 2)

                        # Calculate bar heights and colors
                        left_bar_height = int(left_vertical_travel * VERTICAL_SCALE_FACTOR)
                        right_bar_height = int(right_vertical_travel * VERTICAL_SCALE_FACTOR)
                        
                        color_left_bar = get_color_for_distance(abs(left_vertical_travel))
                        color_right_bar = get_color_for_distance(abs(right_vertical_travel))

                        # Draw bars (OpenCV y-axis is inverted, so we subtract height)
                        cv2.line(display_image, (left_bar_x, zero_y), (left_bar_x, zero_y - left_bar_height), color_left_bar, 10)
                        cv2.line(display_image, (right_bar_x, zero_y), (right_bar_x, zero_y - right_bar_height), color_right_bar, 10)

                        # --- DRAWING TILT BAR ---
                        TILT_SCALE_FACTOR = img_width / 4 # How much the bar moves for full lean
                        tilt_bar_y = int(img_height * 0.05)
                        center_x = int(img_width / 2)

                        # Draw zero-marker for the tilt bar
                        cv2.line(display_image, (center_x, tilt_bar_y - 10), (center_x, tilt_bar_y + 10), (0, 0, 0), 2)

                        # Calculate bar length and color
                        tilt_bar_length = int(norm_lean * TILT_SCALE_FACTOR)
                        tilt_color = get_color_for_distance(abs(norm_lean), max_distance=1.0)

                        # Draw the tilt bar
                        cv2.line(display_image, (center_x, tilt_bar_y), (center_x + tilt_bar_length, tilt_bar_y), tilt_color, 10)

            # Display calibration status on the screen
            cv2.putText(display_image, calibration_status.value, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow("Pose Landmarker", display_image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()
        
        print("Resetting vJoy controller to neutral...")
        vjoy_device.set_axis(pyvjoy.HID_USAGE_X, VJOY_CENTER)
        vjoy_device.set_axis(pyvjoy.HID_USAGE_Y, VJOY_CENTER)
        vjoy_device.set_axis(pyvjoy.HID_USAGE_Z, VJOY_CENTER)
        vjoy_device.set_axis(pyvjoy.HID_USAGE_RX, VJOY_CENTER)
        print("Shutdown complete.")
