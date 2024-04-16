import cv2 as cv

from .gui import GuiMainFigure, annotate_frame
from .recognizer import HandRecognizer
from .game_flow.controller import GameController

import time
from argparse import ArgumentParser


def main():
    argparser = ArgumentParser(prog="Rock Paper Scissors Bot")
    argparser.add_argument("-c", "--cam-index", type=int, default=0)
    args = argparser.parse_args()
    cam_index = args.cam_index

    # Open video capture
    video_cap = cv.VideoCapture(cam_index, cv.CAP_DSHOW)
    if not video_cap.isOpened():
        raise RuntimeError("Failed to open video camera")

    video_cap.set(cv.CAP_PROP_FRAME_WIDTH, 1920 / 2)
    video_cap.set(cv.CAP_PROP_FRAME_HEIGHT, 1080 / 2)

    fig = GuiMainFigure()
    fig.show()

    with HandRecognizer() as recognizer:
        controller = GameController(recognizer, use_serial=True)
        while True:
            # Timestamp
            ts = time.time()
            # Get frame
            ret, frame = video_cap.read()

            # Failed to get frame, bail
            if not ret:
                print(f"Did not receive frame on attempt to read.")
                continue

            recognizer.next_frame(frame, ts)

            controller.update()

            fig.update(recognizer, controller)

            annotate_frame(frame, recognizer)
            cv.imshow("Camera", frame)

            # Quit if Q pressed
            if cv.waitKey(1) == ord("q"):
                break


if __name__ == "__main__":
    main()
