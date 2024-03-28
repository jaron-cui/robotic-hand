import cv2 as cv

from gui import RecognizerFigure, annotate_frame
from recognizer import HandRecognizer
from threading import Thread

import time


def main():
    # Open video capture
    video_cap = cv.VideoCapture(0)
    if not video_cap.isOpened():
        raise RuntimeError("Failed to open video camera")

    with HandRecognizer() as recognizer:
        fig = RecognizerFigure(recognizer)
        fig.show()

        while True:
            # Timestamp
            ts_ms = int(time.time() * 1000)
            # Get frame
            ret, frame = video_cap.read()

            # Failed to get frame, bail
            if not ret:
                print(f"Did not receive frame on attempt to read.")
                continue

            recognizer.next_frame(frame, ts_ms)

            annotate_frame(frame, recognizer)

            cv.imshow("Camera", frame)

            # Quit if Q pressed
            if cv.waitKey(1) == ord("q"):
                break

    fig.close()


if __name__ == "__main__":
    main()
