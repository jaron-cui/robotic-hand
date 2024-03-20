import mediapipe as mp
from mediapipe.tasks.python.vision import (
    GestureRecognizer,
    GestureRecognizerOptions,
    RunningMode,
    GestureRecognizerResult,
)
from mediapipe.tasks.python.vision.hand_landmarker import HandLandmark
from mediapipe.python.solutions import (
    drawing_utils as mp_drawing,
    drawing_styles as mp_drawing_styles,
    hands as mp_hands,
)
from mediapipe.framework.formats import landmark_pb2

import _draw

import numpy as np
import cv2 as cv
import time
from typing import Type, Any


DEFAULT_MODEL_PATH = "./models/gesture_recognizer.task"


class HandGesture(Enum):
    NONE = 0,
    ROCK = auto(),
    PAPER = auto(),
    SCISSORS = auto()


class HandRecognizer:
    def __init__(
        self,
        model_path: str = DEFAULT_MODEL_PATH,
        min_hand_detection_confidence: float = 0.1,
        min_hand_presence_confidence: float = 0.3,
        min_tracking_confidence: float = 0.1,
    ):
        # Create gesture recognizer options
        base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
        self.recognizer_options = GestureRecognizerOptions(
            base_options,
            # Live video mode
            running_mode=RunningMode.LIVE_STREAM,
            # Callback for results
            result_callback=self._recognizer_result_cb,
            # Limit the allowed categories
            canned_gesture_classifier_options=mp.tasks.components.processors.ClassifierOptions(
                category_allowlist=["None", "Closed_Fist", "Open_Palm", "Victory"],
            ),
            min_hand_detection_confidence=min_hand_detection_confidence,
            min_hand_presence_confidence=min_hand_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        self._last_result = None

    def run(self):
        """
        Start processing camera frames and detecting hand data.
        Turns on the camera and camera view, and begins processing frames in a loop.
        Breaks when user quits (presses Q).
        """
        # Open video capture
        video_cap = cv.VideoCapture(0)
        if not video_cap.isOpened():
            raise RuntimeError("Failed to open video camera")

        # With recognizer:
        with GestureRecognizer.create_from_options(
            self.recognizer_options
        ) as recognizer:
            # Start recognizing from video frames in loop
            while True:
                # Timestamp
                ts_ms = int(time.time() * 1000)
                # Get frame
                ret, frame = video_cap.read()

                # Failed to get frame, bail
                if not ret:
                    print(f"Did not receive frame on attempt to read.")
                    continue

                # Create MP image and recognize
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                recognizer.recognize_async(mp_image, ts_ms)

                # If hand landmarks detected, draw on top of video frame to be displayed
                if self._last_result and self._last_result.hand_landmarks:
                    _draw.draw_hand_landmarks(frame, self._last_result.hand_landmarks[0])

                # Show annotated video frame
                cv.imshow("Live Video", frame)

                # Quit if Q pressed
                if cv.waitKey(1) == ord("q"):
                    break

    def is_hand_present(self) -> bool:
        """
        True if a hand is present in the latest frame processed, False otherwise.
        """
        return self._last_result and self._last_result.hand_landmarks

    def get_gesture(self) -> HandGesture:
        """
        Get the latest hand gesture detection result.
        Returns a gesture if one was recognized, or the NONE gesture if none was found.
        """
        if not self.is_hand_present():
            return HandGesture.NONE
        mp_gesture = self._last_result.gestures[0][0].category_name
        match mp_gesture:
            case "Closed_Fist":
                return HandGesture.ROCK
            case "Open_Palm":
                return HandGesture.PAPER
            case "Victory":
                return HandGesture.SCISSORS
            case _:
                return HandGesture.NONE

    def get_wrist_screen_y(self) -> float | None:
        """
        Get the latest Y (vertical) position of the hand's wrist in screen space, if any.
        Ranges from 0.0 (top of screen) to 1.0 (bottom of screen), or None if no hand present.
        """
        if not self.is_hand_present():
            return None
        return self._last_result.hand_landmarks[0][0].y

    def _recognizer_result_cb(
        self, result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int
    ):
        """
        Callback for async results from MP gesture recognizer
        """
        self._last_result = result


recog = HandRecognizer()
recog.run()
