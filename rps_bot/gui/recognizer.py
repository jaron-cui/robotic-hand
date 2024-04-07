import matplotlib.pyplot as plt

from recognizer import HandRecognizer
from recognizer import HandGesture


class RecognizerFigure:
    def __init__(self):
        self.fig, (ax0, ax1, ax2) = plt.subplots(3, 1, height_ratios=[3, 3, 1])
        self.hand_height_plt = LiveDataPlot(ax0, min_y=1, max_y=0, time_range_secs=3)
        self.hand_v_plt = LiveDataPlot(ax1, min_y=4, max_y=-4, time_range_secs=3)
        self.gesture_plt = LiveGesturePlot(ax2)

    def show(self):
        plt.ion()
        plt.show()

    def update(self, recognizer: HandRecognizer):
        preds = recognizer.motion_predictor.filtered_from_last_n_secs(3)
        ts = [p[0] for p in preds]
        y = [p[1][0] for p in preds]
        vy = [p[1][1] for p in preds]

        self.hand_height_plt.set_data(ts, y)
        self.hand_v_plt.set_data(ts, vy)

        peaks = recognizer.motion_predictor.peaks_in_window_ts
        self.hand_height_plt.axvlines(peaks)

        gesture = recognizer.get_gesture()
        gesture_score = recognizer.get_gesture_score()
        self.gesture_plt.update_gesture(gesture, gesture_score)

        # Draw
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def close(self):
        plt.close(self.fig)


class LiveDataPlot:
    def __init__(
        self,
        ax: plt.Axes,
        min_y: float,
        max_y: float,
        time_range_secs: float = 5,
        **plot_kwargs,
    ):
        self.time_range_secs = time_range_secs

        self.ax = ax
        [self.line] = self.ax.plot([], [], **plot_kwargs)
        self.ax.set_xlim(-time_range_secs, 0)
        self.ax.set_ylim(min_y, max_y)
        self.ax.set_xticks([])

    def set_data(self, ts: list[float], vals: list[float]):
        """
        Update the plot with a new height sample at timestamp.
        Pass new_height = None if sample was taken but no value is available.
        Timestamps older than the most recent will be ignored.
        """
        self.line.set_xdata(ts)
        self.line.set_ydata(vals)
        # Adjust bounds of time axis.
        # Slides to the right over time. Will appear as if data is shifting left over time.
        if len(ts) > 0:
            self.ax.set_xlim(ts[-1] - self.time_range_secs, ts[-1])

    def axvlines(self, x):
        for val in x:
            self.ax.axvline(val, color="red")


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
