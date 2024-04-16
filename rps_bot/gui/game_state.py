import matplotlib.pyplot as plt

from rps_bot.game_flow.controller import (
    GameController,
    GameStage,
    PlayingState,
    PendingState,
    GameEndState,
)
from rps_bot.recognizer.gestures import GameResult, HandGesture


class LiveGameStatePlot:
    def __init__(self, ax: plt.Axes, **plot_kwargs):
        self.ax = ax
        self.state_text = ax.text(
            0.5,
            0.75,
            "Game state will appear here",
            fontsize="large",
            horizontalalignment="center",
        )
        self.bot_move_text = ax.text(0.2, 0.25, "Bot move here", fontsize="large")
        self.player_move_text = ax.text(0.6, 0.25, "Human move here", fontsize="large")
        self.ax.axis("off")

    def update(self, state: GameStage):
        match state:
            case GameStage.WAITING:
                self.state_text.set(text="Waiting...", backgroundcolor="lightgray")
                self.bot_move_text.set(text="Bot:", backgroundcolor="w")
                self.player_move_text.set(text="Player:", backgroundcolor="w")

            case PlayingState(_):
                self.state_text.set(
                    text="Rock...paper...scissors...", backgroundcolor="lightblue"
                )
            case PendingState(_, bot_move):
                self.state_text.set(text="SHOOT", backgroundcolor="gold")
                self.bot_move_text.set_text(f"Bot: {bot_move.value.upper()}")
            case GameEndState(_, bot_move, player_move, result, gesture_score):
                match result:
                    case GameResult.WIN:
                        text = f"Bot wins"
                        color = "darksalmon"
                        self.bot_move_text.set_backgroundcolor("darksalmon")
                    case GameResult.DRAW:
                        text = f"Draw"
                        color = "lightgray"
                    case GameResult.LOSS:
                        text = f"Player wins"
                        color = "lightgreen"
                        self.player_move_text.set_backgroundcolor("lightgreen")
                    case GameResult.UNKNOWN:
                        text = "Could not determine player move..."
                        color = "lightcoral"

                self.state_text.set(text=text, backgroundcolor=color)
                if result != GameResult.UNKNOWN:
                    self.player_move_text.set_text(
                        f"Player: {player_move.value.upper()} ({gesture_score:.2f})"
                    )
                else:
                    self.player_move_text.set_text(f"Player: ???")
