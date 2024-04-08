import cv2 as cv
import numpy as np

import time

from . import _util


class Tracker:
    def __init__(
        self,
        roi_padding: float,
        min_init_interval_secs: float,
        min_update_interval_secs: float,
    ):
        self._csrt = cv.TrackerCSRT.create()
        # In screen coords, the amount of padding to add around hand region to use as ROI
        self._roi_padding = roi_padding
        # Whether this tracker has been initialized
        self._inited = False
        # The most recent updated ROI, as provided to init or tracked from update
        self._roi_screen = None

        self._min_init_interval_secs = min_init_interval_secs
        self._min_update_interval_secs = min_update_interval_secs
        # Time that these were last performed. Recorded for limiting rate.
        self._last_init_time = time.time()
        self._last_update_time = time.time()

    def is_inited(self):
        return self._inited

    def init_with_landmarks(self, frame: np.array, hand_landmarks: list):
        self._roi_screen = _util.make_screen_roi_from_landmarks(
            hand_landmarks, self._roi_padding
        )

        if time.time() - self._last_init_time >= self._min_init_interval_secs:
            self._last_init_time = time.time()
            self._inited = True
            self._csrt.init(
                frame, _util.bbox_screen_to_cam(self._roi_screen, frame.shape)
            )

    def update(self, image: np.array):
        if time.time() - self._last_update_time >= self._min_update_interval_secs:
            self._last_update_time = time.time()

            ok, bbox = self._csrt.update(image)
            self._roi_screen = (
                _util.bbox_cam_to_screen(bbox, image.shape) if ok else None
            )

    def stop(self):
        self._inited = False
        self._roi_screen = None

    def get_hand_bbox_screen(self) -> list[float] | None:
        return self._roi_screen

    def get_hand_bbox_camera(self, frame_shape) -> list[int] | None:
        return (
            _util.bbox_screen_to_cam(self._roi_screen, frame_shape)
            if self._roi_screen
            else None
        )

    def get_hand_y(self) -> float | None:
        """
        Get the latest Y (vertical) position of the hand in screen space, if any.
        Ranges from 0.0 (top of screen) to 1.0 (bottom of screen).
        Position may be based on direct recognition or tracking, or None if neither is available.
        """
        if self._roi_screen:
            return self._roi_screen[1] + self._roi_screen[3] / 2
        else:
            return None
