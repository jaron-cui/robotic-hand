import mediapipe as mp
from mediapipe.tasks.python.vision import (
    GestureRecognizer,
    GestureRecognizerOptions,
    RunningMode,
    GestureRecognizerResult,
)

import cv2 as cv
import time
import matplotlib.pyplot as plt
from typing import Type, Any
from queue import Queue

from recognizer import _draw
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

        self._last_result = None
        self.results_queue = Queue()
        self._hand_y = None
        self._events = {
            RecognitionResultsUpdated: set(),
            GameOffered: set(),
            Swinging: set(),
            GesturePlayed: set(),
            GameCancelled: set(),
        }

        self.tracking_inited = False

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

        hand_tracker = cv.TrackerCSRT.create()

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

                while not self.results_queue.empty():
                    result, _, ts_ms = self.results_queue.get()
                    self._last_result = result

                    ts = ts_ms / 1000
                    [
                        cb(RecognitionResultsUpdated(ts))
                        for cb in self._events[RecognitionResultsUpdated]
                    ]

                bbox = None
                if self._last_result and self._last_result.hand_landmarks:
                    landmarks = self._last_result.hand_landmarks[0]
                    bbox = _get_hand_bbox(landmarks, frame.shape, padding=0.05)
                    hand_tracker.init(frame, bbox)
                    self.tracking_inited = True

                    self._hand_y = (bbox[1] + bbox[3] / 2) / frame.shape[0]

                    _draw.draw_hand_landmarks(frame, landmarks)
                    cv.rectangle(frame, bbox, (255, 255, 255), 2, 1)
                elif self.tracking_inited:
                    ok, bbox = hand_tracker.update(frame)
                    if ok:
                        # Tracking success
                        cv.rectangle(frame, bbox, (0, 208, 255), 2, 1)
                        self._hand_y = (bbox[1] + bbox[3] / 2) / frame.shape[0]
                    else:
                        self._hand_y = None

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

    def get_gesture(self) -> HandGesture | None:
        """
        Get the latest hand gesture detection result.
        Returns a gesture if one was recognized, or None if the recognizer gave no result.
        Note that the the model's output could itself be 'none'.
        """
        if not self.is_hand_present():
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
        Get the latest Y (vertical) position of the hand's wrist in screen space, if any.
        Ranges from 0.0 (top of screen) to 1.0 (bottom of screen).
        Position may be based on direct recognition or tracking, or None if neither is available.
        """
        return self._hand_y

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
        self.results_queue.put((result, output_image, timestamp_ms))


def _get_hand_bbox(landmarks, frame_shape, padding: float):
    xmin = int((min([landmark.x for landmark in landmarks]) - padding) * frame_shape[1])
    xmax = int((max([landmark.x for landmark in landmarks]) + padding) * frame_shape[1])
    ymin = int((min([landmark.y for landmark in landmarks]) - padding) * frame_shape[0])
    ymax = int((max([landmark.y for landmark in landmarks]) + padding) * frame_shape[0])
    return (xmin, ymin, xmax - xmin, ymax - ymin)
