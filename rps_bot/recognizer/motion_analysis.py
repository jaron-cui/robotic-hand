from collections import deque, namedtuple
from bisect import bisect
import time
from itertools import pairwise

from scipy import signal
import numpy as np
import cv2 as cv

REPREDICT_INTERVAL_SECS = 0.2
REPEATED_PEAK_DIFF_THRESHOLD_SECS = 0.2
DEFAULT_EST_PERIOD = 1

TurningPoint = namedtuple("TurningPoint", ["ts", "type"])


class MotionAnalyzer:
    def __init__(self, window_secs: float):
        # How far back analysis should consider samples from
        self._window_secs = window_secs

        # Most recent timestamps, direct height measurements, and Kalman filtered heights, velocities
        # At corresponding indicies
        self.ts_history: deque[float] = deque(maxlen=200)
        self.measured_history: deque[float] = deque(maxlen=200)
        self.filtered_history: deque[np.array] = deque(maxlen=200)

        # As of most recent prediction...
        # The turning point (peaks/valleys) found in hand height
        self.turning_points: list[TurningPoint] = []
        # The predicted time the move will be played, if motion in progress
        self.move_eta: float = None
        # The estimated phase in the motion, if in progress
        self.est_phase: float = None

        # Set up Kalman filter
        self._kalman = cv.KalmanFilter(2, 1)
        self._kalman.measurementMatrix = np.array([[1, 0]], np.float32)
        self._kalman.transitionMatrix = np.array([[1, 1], [0, 1]], np.float32)
        self._kalman.processNoiseCov = np.array([[1, 0], [0, 1]], np.float32) * 0.1

        # The time that the motion data was last analyzed for predictions. Recorded for limiting rate.
        self._time_last_prediction = time.time()

    def add_sample(self, ts: float, hand_screen_y: float | None):
        """
        Update with a new sample of the hand screen Y at ts.
        If ts is less recent than already seen samples, it is ignored.
        """
        if hand_screen_y:
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
        else:
            self.filtered_history.append(None)

        # Append ts and actual measurement to history
        self.ts_history.append(ts)
        self.measured_history.append(hand_screen_y)

        # Update predictions, if haven't done this work too recently (expensive)
        if time.time() - self._time_last_prediction >= REPREDICT_INTERVAL_SECS:
            self._time_last_prediction = time.time()
            self._update_predictions(ts)

    def filtered_from_last_n_secs(self, n: float) -> list[(float, np.array)]:
        """
        Get a list of all the predicted (smoothed) states from the last n seconds,
        excluding samples where there is none.
        Returns a list of (ts, pred), where pred is 2x1 np array of y, velocity
        """
        if len(self.ts_history) == 0:
            return []
        cutoff_ts = self.ts_history[-1] - n
        cutoff = bisect(self.ts_history, cutoff_ts)
        return [
            (self.ts_history[i], self.filtered_history[i])
            for i in range(cutoff, len(self.ts_history))
            if self.filtered_history[i] is not None
        ]

    def _update_predictions(self, ts: float):
        # Number of evenly spaced samples to resample provided height data points into
        NUM_RESAMPLES = 50

        # RESET PREDICTIONS
        self.est_phase = None
        self.move_eta = None

        # Get filtered samples from within time window of interest
        window_samples = self.filtered_from_last_n_secs(self._window_secs)

        # If too few samples, don't bother
        if len(window_samples) < 5:
            return

        # RESAMPLING
        # Extract just the y values, and resample uniformly (then reshape into 1D)
        window_y_resampled = signal.resample(
            [p[1][0] for p in window_samples], NUM_RESAMPLES
        ).reshape(-1)
        # Timestamps corresponding to resampled values
        window_ts_resampled = np.linspace(
            window_samples[0][0], window_samples[-1][0], NUM_RESAMPLES
        )

        # FIND PEAKS AND VALLEYS (TURNING POINTS)
        # (Reversed because lower y = higher physically)
        peaks, _ = signal.find_peaks(-window_y_resampled, prominence=0.3)
        valleys, _ = signal.find_peaks(window_y_resampled, prominence=0.3)

        # Map indices to actual timestamps
        peaks = window_ts_resampled[peaks]
        valleys = window_ts_resampled[valleys]

        turning_points = [TurningPoint(ts, "peak") for ts in peaks] + [
            TurningPoint(ts, "valley") for ts in valleys
        ]
        turning_points.sort(key=lambda p: p.ts)

        # If first point is a valley, ignore it
        if len(turning_points) > 0 and turning_points[0][1] == "valley":
            turning_points = turning_points[1:]

        # Store in field
        self.turning_points = turning_points

        # Whether each point alternates between peak and valley
        is_alternating = len(turning_points) > 0 and all(
            a.type != b.type for a, b in pairwise(turning_points)
        )

        # LOOK FOR ACTIVE OR RECENT MOTION
        # Look for bobbing motion based on found peaks, and if so, make predictions.
        # Assuming shooting on 4th bob
        # This would contain 4 peaks, 4 valleys, starting with a peak, ending on a valley

        # If points are alternating, and number does not exceed 8 (amount in a full motion; if exceeded, may have missed it),
        # may be a bobbing action, in progress or recently stopped
        motion_detected = is_alternating and len(turning_points) <= 8

        # If motion not detected, stop
        if not motion_detected:
            return

        # ESTIMATE PERIOD
        # If at least 2 points, can estimate the period of the motion
        if len(turning_points) >= 2:
            est_period = (
                (turning_points[-1][0] - turning_points[0][0])
                / (len(turning_points) - 1)
                * 2
            )
        # Otherwise, assume a default
        else:
            est_period = DEFAULT_EST_PERIOD

        # CHECK WHETHER MOTION MAY STILL BE IN PROGRESS
        # Time since the last turning point that's been detected
        time_since_last_point = ts - turning_points[-1][0]
        # If it's been more than a phase since then, assume the motion stopped
        if time_since_last_point > est_period:
            return

        # ESTIMATE PHASE - each point adds half a cycle, then extrapolate for time since last point
        self.est_phase = len(turning_points) * 0.5 + time_since_last_point / est_period

        # ESTIMATE TIME TO PLAY MOVE (time of 4th valley)
        self.move_eta = ts + (4 - self.est_phase) * est_period
