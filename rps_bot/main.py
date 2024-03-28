import cv2 as cv

from gui import RecognizerFigure, annotate_frame
from recognizer import HandRecognizer
from threading import Thread

import time
from argparse import ArgumentParser


def main():
    argparser = ArgumentParser(prog="Rock Paper Scissors Bot")
    argparser.add_argument("-c", "--cam-index", type=int, default=0)
    args = argparser.parse_args()
    cam_index = args.cam_index

    # Open video capture
    video_cap = cv.VideoCapture(cam_index)
    if not video_cap.isOpened():
        raise RuntimeError("Failed to open video camera")

    fig = RecognizerFigure()
    fig.show()

    with HandRecognizer() as recognizer:
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

            fig.update(recognizer)

            annotate_frame(frame, recognizer)
            cv.imshow("Camera", frame)

            # Quit if Q pressed
            if cv.waitKey(1) == ord("q"):
                break

    fig.close()


if __name__ == "__main__":
    main()
