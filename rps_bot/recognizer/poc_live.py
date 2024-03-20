import mediapipe as mp
from mediapipe.tasks.python.vision import (
    GestureRecognizer,
    GestureRecognizerOptions,
    RunningMode,
    GestureRecognizerResult,
)
from mediapipe.tasks.python.vision.hand_landmarker import HandLandmark
from mediapipe.python.solutions import (
    drawing_utils as mp_drawing,
    drawing_styles as mp_drawing_styles,
    hands as mp_hands,
)
from mediapipe.framework.formats import landmark_pb2

import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv
import time

# Path to task model to use
MODEL_PATH = "./models/gesture_recognizer_rps.task"


def main():
    # The most recent result returned by gesture recognizer
    last_result: GestureRecognizerResult = None

    def handle_result(
        result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int
    ):
        nonlocal last_result
        last_result = result

    # Create gesture recognizer options
    base_options = mp.tasks.BaseOptions(model_asset_path=MODEL_PATH)
    options = GestureRecognizerOptions(
        base_options,
        # Live video mode
        running_mode=RunningMode.LIVE_STREAM,
        # Callback for results
        result_callback=handle_result,
        min_hand_detection_confidence=0.1,
        min_hand_presence_confidence=0.3,
        min_tracking_confidence=0.1
    )

    # Initialize info plot:
    # List of bar labels
    gesture_labels = [
        "''",
        "none",
        "rock",
        "paper",
        "scissors",
    ]
    fig = plt.figure()
    # Create bar chart, set values to 0s for now
    bar_plot = plt.bar(gesture_labels, [0 for _ in gesture_labels], color="blue")
    # Set plot y limits to 0.0-1.0.
    plt.ylim(0.0, 1.0)
    # Turn on interactive mode
    plt.ion()

    # Draw first frame
    fig.canvas.draw()

    # Open video capture
    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        print("Failed to open video camera")
        exit()

    # With recognizer:
    with GestureRecognizer.create_from_options(options) as recognizer:
        # Start recognizing from video frames in loop
        while True:
            # Timestamp
            ts_ms = int(time.time() * 1000)
            # Get frame
            ret, frame = cap.read()

            # Failed to get frame, bail
            if not ret:
                print("Did not receive frame, exiting")
                break

            # Create MP image and recognize
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            recognizer.recognize_async(mp_image, ts_ms)

            # If a result has been recorded
            if last_result:
                # Update info plot
                update_info_plot(bar_plot, last_result)
                fig.canvas.draw()
                plt.pause(0.01)

                # If hand landmarks detected, draw on top of video frame to be displayed
                if last_result.hand_landmarks:
                    draw_hand_landmarks(frame, last_result.hand_landmarks[0])
                    cv.putText(frame, f"Wrist Y: {last_result.hand_landmarks[0][0].y}", (50, 50), cv.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255))

            # Show annotated video frame
            cv.imshow("Live Video", frame)

            # Quit if Q pressed
            if cv.waitKey(1) == ord("q"):
                break

    # Cleanup
    plt.ioff()
    cap.release()
    cv.destroyAllWindows()


def update_info_plot(bar_plot, result: GestureRecognizerResult):
    # Update gesture category scores
    if result.gestures:
        gestures = {
            gesture.category_name: gesture.score for gesture in result.gestures[0]
        }
        scores = [
            gestures.get("", 0),
            gestures.get("none", 0),
            gestures.get("rock", 0),
            gestures.get("paper", 0),
            gestures.get("scissors", 0),
        ]
    else:
        scores = [0 for _ in bar_plot]

    for bar, score in zip(bar_plot, scores):
        bar.set_height(score)

# Adapted directly from code example
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

if __name__ == "__main__":
    main()