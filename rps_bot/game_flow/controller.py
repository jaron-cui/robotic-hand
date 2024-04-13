from enum import Enum, auto
import random
from dataclasses import dataclass
import time

from rps_bot.recognizer import HandRecognizer
from rps_bot.recognizer.gestures import GameResult, HandGesture

WAIT_AFTER_SHOOT = 1.5
MAX_WAIT_FOR_GESTURE_RECOGNITION = 2
GAME_RESULTS_PAUSE_SECS = 2.5


class GameController:
    def __init__(self, recognizer: HandRecognizer):
        self.recognizer = recognizer
        self.state = GameStage.WAITING

    def update(self):
        match self.state:
            case GameStage.WAITING:
                self.update_waiting()
            case GameStage.PLAYING:
                self.update_playing()
            case PendingState(_):
                self.update_pending()
            case GameEndState(_):
                self.update_game_end()

    def update_waiting(self):
        if (
            self.recognizer.motion_predictor.est_phase
            and self.recognizer.motion_predictor.est_phase > 0.5
        ):
            self.state = GameStage.PLAYING

    def update_playing(self):
        assert self.state == GameStage.PLAYING

        est_phase = self.recognizer.motion_predictor.est_phase
        # ... control update

        if est_phase is None or est_phase < 0.5:
            self.state = GameStage.WAITING
        elif self.recognizer.motion_predictor.est_phase >= 4:
            self.shoot()

    def shoot(self):
        assert self.state == GameStage.PLAYING

        # Pick the move to play
        bot_move = random.choice(
            [HandGesture.PAPER, HandGesture.ROCK, HandGesture.SCISSORS]
        )
        # ...control update

        # Transition to waiting for result to be recognized
        self.state = PendingState(time.time(), bot_move)

    def update_pending(self):
        assert isinstance(self.state, PendingState)

        time_since_shoot = time.time() - self.state.ts_shoot

        # Wait a moment after shooting before trying to read result
        if time_since_shoot < WAIT_AFTER_SHOOT:
            return

        # Try to determine result
        # Check if a gesture is recognized
        player_move = self.recognizer.get_gesture()
        # If so, compare against own move
        if player_move is not None and player_move != HandGesture.NONE:
            result = self.state.bot_move.versus(player_move)
            # ... control update
            self.state = GameEndState(
                time.time(),
                self.state.bot_move,
                player_move,
                result,
                self.recognizer.get_gesture_score(),
            )
        elif time_since_shoot >= MAX_WAIT_FOR_GESTURE_RECOGNITION:
            # Too much time has passed
            self.state = GameEndState(
                time.time(), self.state.bot_move, player_move, GameResult.UNKNOWN, None
            )

    def update_game_end(self):
        if time.time() - self.state.ts_game_end >= GAME_RESULTS_PAUSE_SECS:
            self.state = GameStage.WAITING


class GameStage(Enum):
    WAITING = auto()
    PLAYING = auto()
    PENDING_RESULT = auto()
    GAME_END = auto()


@dataclass
class PendingState:
    ts_shoot: float
    bot_move: HandGesture


@dataclass
class GameEndState:
    ts_game_end: float
    bot_move: HandGesture
    player_move: HandGesture
    result: GameResult
    gesture_score: float | None
