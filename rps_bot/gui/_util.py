from mediapipe.tasks.python.vision.hand_landmarker import HandLandmark
from mediapipe.python.solutions import (
    drawing_utils as mp_drawing,
    drawing_styles as mp_drawing_styles,
    hands as mp_hands,
)
from mediapipe.framework.formats import landmark_pb2
import numpy as np
import cv2 as cv

from .recognizer import HandRecognizer


def annotate_frame(frame: np.array, recognizer: HandRecognizer):
    landmarks = recognizer.get_hand_landmarks()
    if landmarks:
        _draw_hand_landmarks(frame, landmarks)

    bbox = recognizer.tracker.get_hand_bbox_camera(frame.shape)
    if bbox:
        if recognizer.is_hand_recognized():
            box_color = (255, 255, 255)
        else:
            box_color = (0, 208, 255)
            filtered_sample = recognizer.motion_predictor.filtered_history[-1]
            if filtered_sample is not None:
                filtered_height = int(filtered_sample[0] * frame.shape[0])
                bbox_center_y = bbox[1] + bbox[3] // 2
                diff_y = filtered_height - bbox_center_y
                bbox = (bbox[0], bbox[1] + diff_y, bbox[2], bbox[3])
        cv.rectangle(frame, bbox, box_color, 2, 1)


def _draw_hand_landmarks(frame: np.ndarray, hand_landmarks: list[HandLandmark]):
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
