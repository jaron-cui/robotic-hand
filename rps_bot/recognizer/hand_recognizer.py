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
from .events import *
from .gestures import HandGesture
from .motion_analysis import MotionAnalyzer


DEFAULT_MODEL_PATH = "./models/gesture_recognizer_rps.task"
TRACKER_INIT_MIN_INTERVAL_SECS = 0.3
TRACKER_UPDATE_MIN_INTERVAL_SECS = 0.1
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
            RecognitionResultsUpdated: set(),
            GameOffered: set(),
            Swinging: set(),
            GesturePlayed: set(),
            GameCancelled: set(),
        }

        # Tracker to fill in for MediaPipe when its hand tracking fails
        self._hand_tracker = cv.TrackerCSRT.create()
        # In screen coords, the amount of padding to add around hand region to use as ROI
        self._tracking_roi_padding = tracking_roi_padding
        # Whether this track has been initialized
        self._tracking_inited = False
        # The most recent updated ROI by the tracker
        self._last_tracking_roi = None

        # Time that these were last performed. Recorded for limiting rate.
        self._last_tracking_init_time = time.time()
        self._last_tracking_update_time = time.time()

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
            [
                cb(RecognitionResultsUpdated(self._last_ts))
                for cb in self._events[RecognitionResultsUpdated]
            ]

            if self.get_hand_y() is not None:
                self.motion_predictor.add_sample(self._last_ts, self.get_hand_y())

            # If MediaPipe recognized a hand, and haven't inited tracker too recently
            if (
                self.is_hand_recognized()
                and time.time() - self._last_tracking_init_time
                >= TRACKER_INIT_MIN_INTERVAL_SECS
            ):
                # Reinit tracker with latest frame and the hand bbox
                self._last_tracking_init_time = time.time()
                self._hand_tracker.init(
                    self._last_frame.numpy_view(), self.get_hand_bbox_camera()
                )
                self._tracking_inited = True
                self._last_hand_found_ts = self._last_ts
            # Elif tracking is inited, and haven't updated too recently,
            elif (
                self._tracking_inited
                and time.time() - self._last_tracking_update_time
                >= TRACKER_UPDATE_MIN_INTERVAL_SECS
            ):
                # ...and it hasn't been to long since MediaPipe last found a hand (tracking likely still valid)
                if time.time() - self._last_hand_found_ts <= TRACKER_EXPIRE_TIME_SECS:
                    self._last_tracking_update_time = time.time()
                    ok, bbox = self._hand_tracker.update(self._last_frame.numpy_view())
                    self._last_tracking_roi = list(bbox) if ok else None
                # If exceeded, stop using tracking
                else:
                    self._last_tracking_roi = None

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
            return _util.make_screen_roi_from_landmarks(
                landmarks, self._tracking_roi_padding
            )
        elif self._last_tracking_roi:
            return _util.bbox_cam_to_screen(
                self._last_tracking_roi, self._last_frame.numpy_view().shape
            )
        else:
            return None

    def get_hand_bbox_camera(self) -> list[int] | None:
        if self.is_hand_recognized():
            return _util.bbox_screen_to_cam(
                self.get_hand_bbox_screen(), self._last_frame.numpy_view().shape
            )
        else:
            return self._last_tracking_roi

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
