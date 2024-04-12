import matplotlib.pyplot as plt
import matplotlib.style as mplstyle

import time
from rps_bot.recognizer import HandRecognizer, HandGesture

mplstyle.use(["fast"])


class RecognizerFigure:
    def __init__(self):
        self.fig, axs = plt.subplots(3, 1, height_ratios=[3, 1, 1])
        self.hand_height_plt = LiveDataPlot(axs[0], min_y=1, max_y=0, time_range_secs=3)
        self.gesture_plt = LiveGesturePlot(axs[1])
        self.motion_pred_plot = LiveMotionPredictionPlot(axs[2])

    def show(self):
        plt.ion()
        plt.show()

    def update(self, recognizer: HandRecognizer):
        preds = recognizer.motion_predictor.filtered_from_last_n_secs(3)
        ts = [p[0] for p in preds]
        y = [p[1][0] for p in preds]
        # vy = [p[1][1] for p in preds]

        self.hand_height_plt.set_data(ts, y)

        peaks = [p.ts for p in recognizer.motion_predictor.turning_points]
        self.hand_height_plt.axvlines(peaks)

        gesture = recognizer.get_gesture()
        gesture_score = recognizer.get_gesture_score()
        self.gesture_plt.update_gesture(gesture, gesture_score)

        eta = recognizer.motion_predictor.move_eta
        self.motion_pred_plot.update_phase(
            recognizer.motion_predictor.est_phase or 0,
            f"+{(eta - time.time()):.1f}s" if eta else "Shoot",
        )

        # Draw
        self.fig.canvas.draw_idle()

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
        self.ax.set_xlim(time.time() - self.time_range_secs, time.time())

    def axvlines(self, x):
        for line in self.ax.lines[1:]:
            line.remove()
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


class LiveMotionPredictionPlot:
    def __init__(self, ax: plt.Axes, **plot_kwargs):
        self.ax = ax

        self.bar = ax.barh(0, width=0, height=0.5)

        # Set ticks at each quarter
        ax.set_xticks([0, 1, 2, 3, 4])
        ax.set_xticklabels(["", "Rock...", "Paper...", "Scissors...", "Shoot"])

        # Hide the y-axis
        ax.yaxis.set_visible(False)

        # Adjust layout
        # ax.tigh

    def update_phase(self, phase: float, eta: float):
        # Fill the bar with the specified percentage
        self.bar[0].set_width(phase)
        self.ax.set_xticklabels(self.ax.get_xticklabels()[:-1] + [str(eta)])
