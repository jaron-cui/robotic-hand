import matplotlib.pyplot as plt

from rps_bot.game_flow.controller import (
    GameController,
    GameStage,
    GameEndState,
    PendingState,
)
from rps_bot.recognizer.gestures import GameResult, HandGesture


class LiveGameStatePlot:
    def __init__(self, ax: plt.Axes, **plot_kwargs):
        self.ax = ax
        self.text = ax.text(
            0.5,
            0.5,
            "Game state will appear here",
            fontsize="large",
            horizontalalignment="center",
        )
        self.ax.axis("off")

    def update(self, controller: GameController):
        match controller.state:
            case GameStage.WAITING:
                self.text.set_text("Waiting...")
            case GameStage.PLAYING:
                self.text.set_text("Playing:")
            case PendingState(_, bot_move):
                self.text.set_text(f"SHOOT (Robot played {bot_move.value.upper()}...)")
            case GameEndState(_, bot_move, player_move, result, gesture_score):
                match result:
                    case GameResult.WIN:
                        text = f"Bot wins - {bot_move.value} beats {player_move.value} ({gesture_score:.2f})"
                    case GameResult.DRAW:
                        text = f"Draw - Both {bot_move.value} ({gesture_score:.2f})"
                    case GameResult.LOSS:
                        text = f"Player wins - {player_move.value} ({gesture_score:.2f}) beats {bot_move.value}"
                    case GameResult.UNKNOWN:
                        text = "Could not determine player move..."

                self.text.set_text(text)
