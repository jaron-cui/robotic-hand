from collections import deque
from bisect import bisect
import time
from itertools import pairwise

from scipy import signal
import numpy as np
import cv2 as cv

FIND_PEAKS_INTERVAL_SECS = 0.2
REPEATED_PEAK_DIFF_THRESHOLD_SECS = 0.2


class MotionAnalyzer:
    def __init__(self, window_secs: float):
        self.ts_history = deque(maxlen=200)
        self.measured_history = deque(maxlen=200)
        self.filtered_history = deque(maxlen=200)
        self.turning_points_in_window_ts = []
        self.window_secs = window_secs
        self._time_last_find_peaks = time.time()

        self._kalman = cv.KalmanFilter(2, 1)
        self._kalman.measurementMatrix = np.array([[1, 0]], np.float32)
        self._kalman.transitionMatrix = np.array([[1, 1], [0, 1]], np.float32)
        self._kalman.processNoiseCov = np.array([[1, 0], [0, 1]], np.float32) * 0.1

        self.current_play_eta = None
        self.current_est_phase = None

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
            NUM_RESAMPLES = 50

            # Extract just the y values, and resample uniformly (then reshape into 1D)
            window_y_resampled = signal.resample(
                [p[1][0] for p in find_peaks_window], NUM_RESAMPLES
            ).reshape(-1)
            # Timestamps corresponding to resampled values
            window_ts_resampled = np.linspace(
                find_peaks_window[0][0], find_peaks_window[-1][0], NUM_RESAMPLES
            )

            # Find peaks and valleys
            # (Reversed because lower y = higher physically)
            peaks, _ = signal.find_peaks(-window_y_resampled, prominence=0.3)
            valleys, _ = signal.find_peaks(window_y_resampled, prominence=0.3)

            # Map indices to actual timestamps
            peaks = window_ts_resampled[peaks]
            valleys = window_ts_resampled[valleys]

            turning_points = [(p, "peak") for p in peaks] + [
                (v, "valley") for v in valleys
            ]
            turning_points.sort(key=lambda p: p[0])

            # If first point is a valley, ignore it
            if len(turning_points) > 0 and turning_points[0][1] == "valley":
                turning_points = turning_points[1:]

            self.turning_points_in_window_ts = [p[0] for p in turning_points]

            # Make prediction based on found peaks:
            # Assuming shooting on 4th bob
            # This would contain 4 peaks, 4 valleys, starting with a peak, ending on a valley

            # Whether each point alternates between peak and valley
            # If so, may be a bobbing action
            is_alternating = len(turning_points) > 0 and all(
                a[1] != b[1] for a, b in pairwise(turning_points)
            )

            # If 8 or more points, play may have already been missed - current action is to make no prediction
            if not is_alternating or len(turning_points) >= 8:
                self.current_est_period = None
                self.current_est_phase = None
                self.current_play_eta = None
            else:
                # If at least 2 points, can estimate the period of the motion
                if len(turning_points) >= 2:
                    self.current_est_period = (
                        (turning_points[-1][0] - turning_points[0][0])
                        / (len(turning_points) - 1)
                        * 2
                    )
                else:
                    self.current_est_period = 1

                # Estimate phase - each point adds half a cycle, then extrapolate for time since last point
                # But if it's been more than a phase since the last phase, assume stopped
                time_since_last_point = ts - turning_points[-1][0]
                if time_since_last_point < self.current_est_period:
                    self.current_est_phase = (
                        len(turning_points) * 0.5
                        + time_since_last_point / self.current_est_period
                    )

                    # Estimate time to play move (time of 4th valley)
                    self.current_play_eta = (
                        ts + (4 - self.current_est_phase) * self.current_est_period
                    )
                else:
                    self.current_est_phase = None
                    self.current_play_eta = None

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
