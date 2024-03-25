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
    hand_landmarks_proto.landmark.extend([
        landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks
    ])
    mp_drawing.draw_landmarks(
        frame,
        hand_landmarks_proto,
        mp_hands.HAND_CONNECTIONS,
        mp_drawing_styles.get_default_hand_landmarks_style(),
        mp_drawing_styles.get_default_hand_connections_style(),
    )

class LiveHandHeightPlot:
    def __init__(self, min_h: float, max_h: float, time_range_secs: float, **plot_kwargs):
        self.time_range_secs = time_range_secs
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], **plot_kwargs)
        self.ax.set_xlim(0)
        self.ax.set_ylim(min_h, max_h)

    def update_hand_height_plot(self, ts: float, new_height: float | None):
        # If there's a new height at this time, add it to plot
        if new_height is not None:
            self.line.set_xdata(np.append(self.line.get_xdata(), ts))
            self.line.set_ydata(np.append(self.line.get_ydata(), new_height))
        # Adjust bounds of time axis.
        # Slides to the right over time, except at the beginning when span is too short.
        new_xmax = max(self.ax.get_xlim()[1], ts)
        new_xmin = max(0, new_xmax - self.time_range_secs)
        self.ax.set_xlim(new_xmin, new_xmax)

        # Draw
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def close(self):
        plt.close(self.fig)
    