import pyqtgraph as pg
import numpy as np

import time

from rps_bot.recognizer import HandRecognizer, HandGesture


class RecognizerFigureQt:
    def __init__(self, time_range_secs: int = 3):
        self.time_range_secs = time_range_secs

        self.app = pg.mkQApp("RPS Bot")
        win = pg.GraphicsLayoutWidget(show=True)

        p1 = win.addPlot(title="Hand height")
        p1.setYRange(1, 0)
        p1.invertY(True)
        p1.showAxes((True, False, False, True), showValues=(True, False, False, False))
        self.curve1: pg.PlotCurveItem = p1.plot()

        win.nextRow()
        self.gesture_label = win.addLabel(
            "Gesture prediction will appear here", size="16pt"
        )

        win.nextRow()
        p2 = win.addPlot()
        p2.setXRange(0, 4)
        p2.hideAxis("left")
        p2.getAxis("bottom").setTicks(
            [[(0, "..."), (1, "rock"), (2, "paper"), (3, "scissors"), (4, "shoot")]]
        )
        self.phase_bar = pg.BarGraphItem(x0=0, width=0, y0=0, height=1)
        p2.addItem(self.phase_bar)

        self.win = win
        self.p1 = p1
        self.p2 = p2

        self.inflines = []

    def update(self, recognizer: HandRecognizer):
        preds = recognizer.motion_predictor.filtered_from_last_n_secs(
            self.time_range_secs
        )
        ts = np.array([p[0] for p in preds])
        y = np.array([p[1][0] for p in preds]).reshape(-1)
        peaks = [p.ts for p in recognizer.motion_predictor.turning_points]

        self.curve1.setData(x=ts, y=y)
        self.p1.setXRange(time.time() - self.time_range_secs, time.time())

        for p in self.inflines:
            self.p1.removeItem(p)
        for p in peaks:
            inf = pg.InfiniteLine(pos=p, angle=90)
            self.p1.addItem(inf)
            self.inflines.append(inf)

        gesture = recognizer.get_gesture()
        gesture_score = recognizer.get_gesture_score()
        if gesture is None:
            self.gesture_label.setText(f"Gesture Prediction: (No prediction)")
        else:
            self.gesture_label.setText(
                f"Gesture Prediction: {gesture.value} ({gesture_score:.2f})"
            )

        self.phase_bar.setOpts(
            x0=0, width=recognizer.motion_predictor.est_phase or 0, height=1
        )
