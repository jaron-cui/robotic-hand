from mediapipe.tasks.python.vision.hand_landmarker import HandLandmark
from mediapipe.python.solutions import (
    drawing_utils as mp_drawing,
    drawing_styles as mp_drawing_styles,
    hands as mp_hands,
)
from mediapipe.framework.formats import landmark_pb2
import numpy as np

def draw_hand_landmarks(frame: np.ndarray, hand_landmarks: list[HandLandmark]):
    """
    Draw hand landmarks on the given frame.
    Adapted directly from MP code example.
    """
    hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
    hand_landmarks_proto.landmark.extend(
        [
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z)
            for landmark in hand_landmarks
        ]
    )
    mp_drawing.draw_landmarks(
        frame,
        hand_landmarks_proto,
        mp_hands.HAND_CONNECTIONS,
        mp_drawing_styles.get_default_hand_landmarks_style(),
        mp_drawing_styles.get_default_hand_connections_style(),
    )
