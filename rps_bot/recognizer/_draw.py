from mediapipe.tasks.python.vision.hand_landmarker import HandLandmark
from mediapipe.python.solutions import (
    drawing_utils as mp_drawing,
    drawing_styles as mp_drawing_styles,
    hands as mp_hands,
)
from mediapipe.framework.formats import landmark_pb2
import numpy as np
import matplotlib.pyplot as plt

# Adapted directly from MP code example
def draw_hand_landmarks(frame: np.ndarray, hand_landmarks: list[HandLandmark]):
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


class LiveHandHeightPlot:
    def __init__(
        self,
        fig: plt.Figure,
        ax: plt.Axes,
        min_h: float,
        max_h: float,
        time_range_secs: float,
        **plot_kwargs,
    ):
        self.time_range_secs = time_range_secs
        self.times, self.heights = [], []

        self.fig, self.ax = fig, ax
        (self.line,) = self.ax.plot(self.times, self.heights, **plot_kwargs)
        self.ax.set_xlim(-time_range_secs, 0)
        self.ax.set_ylim(min_h, max_h)
        self.ax.set_xticks([])

    def update_hand_height(self, ts: float, new_height: float | None):
        if len(self.times) > 0:
            latest_time = max(ts, self.times[-1])
        else:
            latest_time = ts

        # If time is at least as new as most recent, add it to plot
        if ts >= latest_time:
            self.times.append(ts)
            self.heights.append(new_height)
            self.line.set_xdata(self.times)
            self.line.set_ydata(self.heights)
        # Adjust bounds of time axis.
        # Slides to the right over time. Will appear as if data is shifting left over time.
        if len(self.times) > 0:
            self.ax.set_xlim(latest_time - self.time_range_secs, latest_time)


class LiveGesturePlot:
    def __init__(self, fig: plt.Figure, ax: plt.Axes, **plot_kwargs):
        self.fig, self.ax = fig, ax
        self.text = ax.text(
            0.5,
            0.5,
            "Gesture Prediction: None yet",
            fontsize="large",
            horizontalalignment="center",
        )
        self.ax.axis("off")

    def update_gesture(self, gesture_name: str, score: float):
        gesture_name = gesture_name or "none"
        self.text.set_text(f"Gesture Prediction: {gesture_name} ({score:.2f})")
