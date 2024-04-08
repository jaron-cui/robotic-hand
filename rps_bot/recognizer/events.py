from mediapipe.tasks.python.vision import GestureRecognizerResult

from dataclasses import dataclass

from .gestures import HandGesture


class GameOffered:
    """
    Detected the player initiating a game, by holding a fist still at the camera.
    """

    def __init__(self):
        pass


class Swinging:
    """
    Detected the player's hand swinging, preparing to shoot.
    Occurs whenever the motion prediction has been updated.
    Contains data about the hand's current and predicted motion.
    """

    def __init__(self, ts: float, est_period_secs: float, est_current_phase: float):
        self.ts = ts
        """Timestamp of this data, from time()."""
        self.est_period_secs = est_period_secs
        """The estimated time (secs) taken for each full swing in the periodic motion,
        i.e. time to move "to and back"."""
        self.est_current_phase = est_current_phase
        """The estimated current phase in the periodic motion, i.e. which part of which swing
        the hand is on. Each whole phase occurs at the apex.

        For example:
        1.0 = 1 swing completed (hand at top),
        1.5 = midway through 2nd swing (hand at bottom)."""


class GesturePlayed:
    """Detected the hand play their gesture in the game, after finishing the swings."""

    def __init__(self, gesture: HandGesture):
        self.gesture = gesture
        """The gesture played. May be NONE if not recognized."""


class GameCancelled:
    """The player didn't finish the started motion, or the recognizer failed."""

    def __init__(self):
        pass
