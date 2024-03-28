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
import numpy as np

from recognizer import _util
from recognizer.events import *
from recognizer.gestures import HandGesture


DEFAULT_MODEL_PATH = "./models/gesture_recognizer_rps.task"


class HandRecognizer:
    def __init__(
        self,
        model_path: str = DEFAULT_MODEL_PATH,
        min_hand_detection_confidence: float = 0.5,
        min_hand_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        tracking_roi_padding: float = 0.05,
    ):
        # Create gesture recognizer options
        base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
        self.recognizer_options = GestureRecognizerOptions(
            base_options,
            # Live video mode
            running_mode=RunningMode.LIVE_STREAM,
            # Callback for results
            result_callback=self._recognizer_result_cb,
            min_hand_detection_confidence=min_hand_detection_confidence,
            min_hand_presence_confidence=min_hand_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        self._results_queue = Queue()
        self._last_result = None
        self._last_frame = None

        self._events = {
            RecognitionResultsUpdated: set(),
            GameOffered: set(),
            Swinging: set(),
            GesturePlayed: set(),
            GameCancelled: set(),
        }

        self.hand_tracker = cv.TrackerCSRT.create()
        self.tracking_roi_padding = tracking_roi_padding
        self.tracking_inited = False
        self._last_tracking_roi = None

    def __enter__(self):
        self.mp_recognizer = GestureRecognizer.create_from_options(
            self.recognizer_options
        )
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.mp_recognizer.close()

    def next_frame(self, frame, ts_ms: int):
        # Create MP image and recognize
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        self.mp_recognizer.recognize_async(mp_image, ts_ms)

        while not self._results_queue.empty():
            self._last_result, self._last_frame, ts_ms = self._results_queue.get()

            ts = ts_ms / 1000
            [
                cb(RecognitionResultsUpdated(ts))
                for cb in self._events[RecognitionResultsUpdated]
            ]

        if self.is_hand_recognized():
            self.hand_tracker.init(self._last_frame.numpy_view(), self.get_hand_bbox_camera())
            self.tracking_inited = True
        elif self.tracking_inited:
            ok, bbox = self.hand_tracker.update(self._last_frame.numpy_view())
            self._last_tracking_roi = list(bbox) if ok else None

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

    def get_hand_y(self) -> float | None:
        """
        Get the latest Y (vertical) position of the hand in screen space, if any.
        Ranges from 0.0 (top of screen) to 1.0 (bottom of screen).
        Position may be based on direct recognition or tracking, or None if neither is available.
        """
        bbox = self.get_hand_bbox_screen()
        if bbox:
            return bbox[1] + bbox[3] / 2
        else:
            return None

    def get_hand_bbox_screen(self) -> list[float] | None:
        if self.is_hand_recognized():
            landmarks = self.get_hand_landmarks()
            xmin = (
                min([landmark.x for landmark in landmarks]) - self.tracking_roi_padding
            )
            xmax = (
                max([landmark.x for landmark in landmarks]) + self.tracking_roi_padding
            )
            ymin = (
                min([landmark.y for landmark in landmarks]) - self.tracking_roi_padding
            )
            ymax = (
                max([landmark.y for landmark in landmarks]) + self.tracking_roi_padding
            )
            return [xmin, ymin, xmax - xmin, ymax - ymin]
        elif self._last_tracking_roi:
            return _util.bbox_cam_to_screen(self._last_tracking_roi, self._last_frame.numpy_view().shape)
        else:
            return None

    def get_hand_bbox_camera(self) -> list[int] | None:
        if self.is_hand_recognized():
            return _util.bbox_screen_to_cam(self.get_hand_bbox_screen(), self._last_frame.numpy_view().shape)
        else:
            return self._last_tracking_roi

    def get_hand_landmarks(self) -> list[HandLandmark] | None:
         return self._last_result.hand_landmarks[0] if self.is_hand_recognized() else None

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