from collections import deque
from bisect import bisect
import time

from scipy import signal
import numpy as np
import cv2 as cv

FIND_PEAKS_INTERVAL_SECS = 0.2


class MotionAnalyzer:
    def __init__(self, window_secs: float):
        self.ts_history = deque(maxlen=200)
        self.measured_history = deque(maxlen=200)
        self.filtered_history = deque(maxlen=200)
        self.peaks_in_window_ts = []
        self.window_secs = window_secs
        self._time_last_find_peaks = time.time()

        self._kalman = cv.KalmanFilter(2, 1)
        self._kalman.measurementMatrix = np.array([[1, 0]], np.float32)
        self._kalman.transitionMatrix = np.array([[1, 1], [0, 1]], np.float32)
        self._kalman.processNoiseCov = np.array([[1, 0], [0, 1]], np.float32) * 0.05

    def add_sample(self, ts: float, hand_screen_y: float):
        """
        Update with a new sample of the hand screen Y at ts.
        If ts is less recent than already seen samples, it is ignored.
        """
        # If there's been any previous samples
        if len(self.ts_history) > 0:
            # Time delta from last sample
            dt = self.ts_history[-1] - ts
            # Update transition matrix to account for varying time delta
            self._kalman.transitionMatrix = np.array([[1, dt], [0, 1]], np.float32)
        # Kalman predict
        self._kalman.predict()
        # Kalman correct with sample
        self._kalman.correct(np.array([[hand_screen_y]], np.float32))
        # Append filtered state to history
        self.filtered_history.append(self._kalman.statePost)

        # Append ts and actual measurement to history
        self.ts_history.append(ts)
        self.measured_history.append(hand_screen_y)

        # Find peaks in the y history:
        # Get filtered samples from within time window of interest
        find_peaks_window = self.filtered_from_last_n_secs(self.window_secs)
        # If long enough, and haven't done this work too recently (expensive),
        if (
            len(find_peaks_window) > 5
            and time.time() - self._time_last_find_peaks >= FIND_PEAKS_INTERVAL_SECS
        ):
            NUM_RESAMPLES = 100

            # Extract just the y values, and resample uniformly (then reshape into 1D)
            window_y_resampled = signal.resample(
                [p[1][0] for p in find_peaks_window], NUM_RESAMPLES
            ).reshape(-1)
            # Timestamps corresponding to resampled values
            window_ts_resampled = np.linspace(
                find_peaks_window[0][0], find_peaks_window[-1][0], NUM_RESAMPLES
            )
            peaks, _ = signal.find_peaks(-window_y_resampled, prominence=0.3)
            self.peaks_in_window_ts = window_ts_resampled[peaks]
            print(self.peaks_in_window_ts)

            # Reset last find peaks time
            self._time_last_find_peaks = time.time()

    def filtered_from_last_n_secs(self, n: float) -> list[(float, np.array)]:
        """
        Get a list of all the predicted (smoothed) states from the last n seconds.
        Returns a list of (ts, pred), where pred is 2x1 np array of y, velocity
        """
        if len(self.ts_history) == 0:
            return []
        cutoff_ts = self.ts_history[-1] - n
        cutoff = bisect(self.ts_history, cutoff_ts)
        return [
            (self.ts_history[i], self.filtered_history[i])
            for i in range(cutoff, len(self.ts_history))
        ]
