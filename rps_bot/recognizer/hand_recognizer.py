import mediapipe as mp
from mediapipe.tasks.python.vision import (
    GestureRecognizer,
    GestureRecognizerOptions,
    RunningMode,
    GestureRecognizerResult,
)
from mediapipe.tasks.python.vision.hand_landmarker import HandLandmark

import cv2 as cv
import time
from typing import Type
from queue import Queue

from . import _util
from .tracker import Tracker
from .events import *
from .gestures import HandGesture
from .motion_analysis import MotionAnalyzer


DEFAULT_MODEL_PATH = "./models/gesture_recognizer_rps.task"
TRACKER_INIT_MIN_INTERVAL_SECS = 0.3
TRACKER_UPDATE_MIN_INTERVAL_SECS = 0.15
TRACKER_EXPIRE_TIME_SECS = 1


class HandRecognizer:
    def __init__(
        self,
        model_path: str = DEFAULT_MODEL_PATH,
        min_hand_detection_confidence: float = 0.5,
        min_hand_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        tracking_roi_padding: float = 0.05,
    ):
        # Responsible to analyzing hand motion to detect games
        self.motion_predictor = MotionAnalyzer(5)

        # Create gesture recognizer options
        base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
        self._recognizer_options = GestureRecognizerOptions(
            base_options,
            # Live video mode
            running_mode=RunningMode.LIVE_STREAM,
            # Callback for results
            result_callback=self._recognizer_result_cb,
            min_hand_detection_confidence=min_hand_detection_confidence,
            min_hand_presence_confidence=min_hand_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        # Results from MediaPipe added here for use
        self._results_queue = Queue()
        self._last_result = None
        self._last_frame = None
        self._last_ts = None
        self._last_hand_found_ts = None

        # Dict of event type to its set of callbacks
        self._events = {
            GameOffered: set(),
            Swinging: set(),
            GesturePlayed: set(),
            GameCancelled: set(),
        }

        # Tracker to fill in for MediaPipe when its hand tracking fails
        self.tracker = Tracker(
            tracking_roi_padding,
            TRACKER_INIT_MIN_INTERVAL_SECS,
            TRACKER_UPDATE_MIN_INTERVAL_SECS,
        )

    def __enter__(self):
        self.mp_recognizer = GestureRecognizer.create_from_options(
            self._recognizer_options
        )
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.mp_recognizer.close()

    def next_frame(self, frame, ts: float):
        # Create MP image and recognize
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        self.mp_recognizer.recognize_async(mp_image, int(ts * 1000))

        while not self._results_queue.empty():
            self._last_result, self._last_frame, result_ts_ms = (
                self._results_queue.get()
            )

            self._last_ts = result_ts_ms / 1000

            # If MediaPipe recognized a hand
            if self.is_hand_recognized():
                # Reinit tracker with latest frame and the hand bbox
                self.tracker.init_with_landmarks(
                    self._last_frame.numpy_view(), self.get_hand_landmarks()
                )
                self._last_hand_found_ts = self._last_ts
            # Elif tracking is inited
            elif self.tracker.is_inited():
                # ...and it hasn't been to long since MediaPipe last found a hand (tracking likely still valid)
                if time.time() - self._last_hand_found_ts <= TRACKER_EXPIRE_TIME_SECS:
                    self.tracker.update(self._last_frame.numpy_view())
                # If exceeded, stop using tracking
                else:
                    self.tracker.stop()

            self.motion_predictor.add_sample(self._last_ts, self.tracker.get_hand_y())

    def is_hand_recognized(self) -> bool:
        """
        True if a hand is directly recognized in the latest frame processed, False otherwise.
        Not necessarily True when hand is present or when tracking is successful.
        """
        return self._last_result and self._last_result.hand_landmarks

    def get_gesture(self) -> HandGesture | None:
        """
        Get the latest hand gesture detection result.
        Returns a gesture if one was recognized, or None if the recognizer gave no result.
        Note that the the model's output could itself be 'none'.
        """
        if not self.is_hand_recognized():
            return None
        mp_gesture = self._last_result.gestures[0][0].category_name
        match mp_gesture:
            case "rock":
                return HandGesture.ROCK
            case "paper":
                return HandGesture.PAPER
            case "scissors":
                return HandGesture.SCISSORS
            case "none":
                return HandGesture.NONE
            case _:
                return None

    def get_gesture_score(self) -> float | None:
        if self.get_gesture() is not None:
            return self._last_result.gestures[0][0].score
        else:
            return None

    def get_hand_landmarks(self) -> list[HandLandmark] | None:
        return (
            self._last_result.hand_landmarks[0] if self.is_hand_recognized() else None
        )

    def add_event_listener(self, event_type: Type, callback):
        """
        Register a callback for when the specified event type occurs.
        callback should accept an event of the given type as argument.
        """
        try:
            self._events[event_type].add(callback)
        except KeyError:
            raise ValueError(
                f"{event_type} is not an event raised by {self.__class__.__name__}"
            )

    def remove_event_listener(self, event_type: Type, callback):
        """
        Unregister a callback for the specified event type, stop receiving calls.
        Does nothing if not already registered.
        """
        try:
            event_listeners = self._events[event_type]
        except KeyError:
            raise ValueError(
                f"{event_type.__name__} is not an event raised by {self.__class__.__name__}"
            )

        try:
            event_listeners.remove(callback)
        except KeyError:
            pass

    def _recognizer_result_cb(
        self, result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int
    ):
        """
        Callback for async results from MP gesture recognizer
        """
        self._results_queue.put((result, output_image, timestamp_ms))
