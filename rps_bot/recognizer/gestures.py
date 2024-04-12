from enum import Enum, auto


class GameResult(Enum):
    WIN = "auto()"
    DRAW = auto()
    LOSS = auto()
    UNKNOWN = auto()


class HandGesture(Enum):
    NONE = "none"
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"

    def versus(self, other) -> GameResult:
        if self == HandGesture.NONE or other == HandGesture.NONE:
            raise ValueError(
                f"A move in an RPS comparison was None: {self} vs. {other}"
            )

        if self == other:
            return GameResult.DRAW

        match self, other:
            case (
                (HandGesture.ROCK, HandGesture.SCISSORS)
                | (HandGesture.SCISSORS, HandGesture.PAPER)
                | (HandGesture.PAPER, HandGesture.ROCK)
            ):
                return GameResult.WIN
            case _:
                return GameResult.LOSS
