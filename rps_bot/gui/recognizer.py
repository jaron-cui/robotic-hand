import numpy as np
import matplotlib.pyplot as plt
import time

from recognizer import HandRecognizer
from recognizer import HandGesture
from recognizer.events import RecognitionResultsUpdated

class RecognizerFigure:
    def __init__(self):
        self.fig, (ax0, ax1) = plt.subplots(2, 1, height_ratios=[3, 1])
        self.hand_height_plt = LiveHandHeightPlot(
            ax0, min_h=1, max_h=0, time_range_secs=5
        )
        self.gesture_plt = LiveGesturePlot(ax1)

    def show(self):
        plt.ion()
        plt.show()

    def update(self, recognizer: HandRecognizer):
        hand_height = recognizer.get_hand_y()
        self.hand_height_plt.update_hand_height(time.time(), hand_height)

        gesture = recognizer.get_gesture()
        gesture_score = recognizer.get_gesture_score()
        self.gesture_plt.update_gesture(gesture, gesture_score)

        # Draw
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


    def close(self):
        plt.close(self.fig)


class LiveHandHeightPlot:
    def __init__(
        self,
        ax: plt.Axes,
        min_h: float,
        max_h: float,
        time_range_secs: float = 5,
        **plot_kwargs,
    ):
        self.time_range_secs = time_range_secs
        self.times, self.heights = [], []

        self.ax = ax
        [self.line] = self.ax.plot(self.times, self.heights, **plot_kwargs)
        self.ax.set_xlim(-time_range_secs, 0)
        self.ax.set_ylim(min_h, max_h)
        self.ax.set_xticks([])

    def update_hand_height(self, ts: float, new_height: float | None):
        """
        Update the plot with a new height sample at timestamp.
        Pass new_height = None if sample was taken but no value is available.
        Timestamps older than the most recent will be ignored.
        """
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
    def __init__(self, ax: plt.Axes, **plot_kwargs):
        self.ax = ax
        self.text = ax.text(
            0.5,
            0.5,
            "Gesture Prediction: None yet",
            fontsize="large",
            horizontalalignment="center",
        )
        self.ax.axis("off")

    def update_gesture(self, gesture: HandGesture | None, score: float | None):
        if gesture is None:
            self.text.set_text(f"Gesture Prediction: (No prediction)")
        else:
            self.text.set_text(f"Gesture Prediction: {gesture.value} ({score:.2f})")
