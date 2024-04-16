import signal
import sys

import cv2 as cv

from rps_bot.hand_serial import RPSSerial
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

    serial = RPSSerial(port='COM3', eport='COM4')

    def shutdown_handler(_, __):
        # This function will be called when Ctrl+C is pressed
        print("Shutting down")
        serial.close()
        sys.exit(0)
    signal.signal(signal.SIGINT, shutdown_handler)

    # Open video capture
    video_cap = cv.VideoCapture(cam_index, cv.CAP_DSHOW)
    if not video_cap.isOpened():
        raise RuntimeError("Failed to open video camera")

    video_cap.set(cv.CAP_PROP_FRAME_WIDTH, 1920 / 2)
    video_cap.set(cv.CAP_PROP_FRAME_HEIGHT, 1080 / 2)

    input('Verify that the elbow is at the lowest position. [Enter to proceed]')
    input('Verify that the finger winch gears are coupled. [Enter to proceed]')
    serial.recalibrate()

    fig = GuiMainFigure()
    fig.show()

    with HandRecognizer() as recognizer:
        controller = GameController(recognizer, serial)
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

            fig.update(recognizer, controller.state)

            annotate_frame(frame, recognizer)
            cv.imshow("Camera", frame)

            # Quit if Q pressed
            if cv.waitKey(1) == ord("q"):
                break


if __name__ == "__main__":
    main()
