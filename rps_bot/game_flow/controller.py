from enum import Enum, auto
import random
from dataclasses import dataclass
import time

from rps_bot.recognizer import HandRecognizer
from rps_bot.recognizer.gestures import GameResult, HandGesture
from rps_bot.hand_serial import RPSSerial

WAIT_AFTER_SHOOT = 2
MAX_WAIT_FOR_GESTURE_RECOGNITION = 2
GAME_RESULTS_PAUSE_SECS = 3
# How much in advance control signals should be sent before the actual require time
# i.e. the control delay.
CONTROL_PREEMPT_SECS = 2


class GameController:
    def __init__(self, recognizer: HandRecognizer, serial: RPSSerial = None):
        self.recognizer = recognizer
        self.state = GameStage.WAITING
        self.serial = serial

    def update(self):
        match self.state:
            case GameStage.WAITING:
                self.update_waiting()
            case PlayingState(_):
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
            self.state = PlayingState(started_shoot_move=None)

    def update_playing(self):
        assert isinstance(self.state, PlayingState)

        est_phase = self.recognizer.motion_predictor.est_phase

        if est_phase is None or est_phase < 0.5:
            self.state = GameStage.WAITING
        elif self.state.started_shoot_move is None:
            self.bob_if_needed()
            if est_phase >= self.delay_compensate_phase(4, CONTROL_PREEMPT_SECS):
                self.start_shoot_movement()
        elif est_phase >= 4:
            self.shoot()

    def bob_if_needed(self):
        assert isinstance(self.state, PlayingState)

        if (
            self.state.last_bob_time is None
            or time.time() - self.state.last_bob_time
            >= self.recognizer.motion_predictor.est_period
        ):
            self.state.last_bob_time = time.time()
            if self.serial:
                self.serial.bob()

    def start_shoot_movement(self):
        assert (
            isinstance(self.state, PlayingState)
            and self.state.started_shoot_move is None
        )

        # Pick the move to play
        bot_move = random.choice([HandGesture.ROCK, HandGesture.SCISSORS])
        # Set control to make gesture
        if self.serial:
            match bot_move:
                case HandGesture.ROCK:
                    self.serial.rock()
                case HandGesture.PAPER:
                    self.serial.paper()
                case HandGesture.SCISSORS:
                    self.serial.scissors()

        self.state.started_shoot_move = bot_move

    def shoot(self):
        assert isinstance(self.state, PlayingState)

        # If haven't started bot movement yet (no preempt), do it now
        if self.state.started_shoot_move is None:
            self.start_shoot_movement()

        # Transition to waiting for result to be recognized
        self.state = PendingState(time.time(), self.state.started_shoot_move)

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
            # Reset robot hand gesture
            if self.serial:
                self.serial.paper()
            # Transition back to waiting state
            self.state = GameStage.WAITING

    def delay_compensate_phase(self, phase: int, control_delay: float):
        """"""
        control_delay_phases = (
            control_delay / self.recognizer.motion_predictor.est_period
        )
        # Clamp neg values to 0
        return max(0, phase - control_delay_phases)


class GameStage(Enum):
    WAITING = auto()


@dataclass
class PlayingState:
    started_shoot_move: HandGesture | None
    last_bob_time = None


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
