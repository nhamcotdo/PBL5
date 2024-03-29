import cv2
import numpy as np
import mediapipe as mp
import json

f = open('setting.json')
setting = json.load(f)

# Actions that we try to detect
actions = setting['actions']

sequence_length = setting['sequence_length']
threshold = setting['threshold']
mp_holistic = mp.solutions.holistic # Holistic model
mp_drawing = mp.solutions.drawing_utils # Drawing utilities


def draw_styled_landmarks(image, results):
    # Draw pose connections
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
                             mp_drawing.DrawingSpec(color=(80,22,10), thickness=2, circle_radius=4), 
                             mp_drawing.DrawingSpec(color=(80,44,121), thickness=2, circle_radius=2)
                             ) 
    # Draw left hand connections
    mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS, 
                             mp_drawing.DrawingSpec(color=(121,22,76), thickness=2, circle_radius=4), 
                             mp_drawing.DrawingSpec(color=(121,44,250), thickness=2, circle_radius=2)
                             ) 
    # Draw right hand connections  
    mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS, 
                             mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=4), 
                             mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                             ) 

def mediapipe_detection(image, model):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) # COLOR CONVERSION BGR 2 RGB
    image.flags.writeable = False                  # Image is no longer writeable
    results = model.process(image)                 # Make prediction
    image.flags.writeable = True                   # Image is now writeable 
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) # COLOR COVERSION RGB 2 BGR
    return image, results

def extract_keypoints(results):
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33*4)
    lh = np.array([[res.x, res.y, res.z, res.visibility] for res in results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21*4)
    rh = np.array([[res.x, res.y, res.z, res.visibility] for res in results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(21*4)

    return np.concatenate([pose, lh, rh])

def frames_extraction(video_path):
    video_reader = cv2.VideoCapture(video_path)
    video_frames_count = 0
    s, f = video_reader.read()
    while s:
        s, f = video_reader.read()
        video_frames_count += 1
    video_reader.release()

    if video_frames_count < sequence_length:
        return []
    skip_frames = int(0.1 * video_frames_count)
    skip_frames_window = max(int((video_frames_count - skip_frames*2) /sequence_length), 1)

    # Danh sách chứa các frame sẽ lấy
    video_keypoints = []

    cap = cv2.VideoCapture(video_path)
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        for frame_counter in range(sequence_length):
            cap.set(cv2.CAP_PROP_POS_FRAMES,
                    skip_frames + frame_counter * skip_frames_window)
            
            ret, frame = cap.read()
            if not ret:
                print('eror')
                continue

            image, results = mediapipe_detection(frame, holistic)
            draw_styled_landmarks(image, results)   

            keypoints = extract_keypoints(results)
            video_keypoints.append(keypoints)
    cap.release()
    cv2.destroyAllWindows()
    return video_keypoints