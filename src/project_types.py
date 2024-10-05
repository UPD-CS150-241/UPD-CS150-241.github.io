from __future__ import annotations
from typing import NewType
from dataclasses import dataclass
from enum import StrEnum, IntEnum, auto


PlayerId = NewType('PlayerId', int)


class Rank(StrEnum):
    ACE = 'Ace'
    TWO = 'Two'
    THREE = 'Three'
    FOUR = 'Four'
    FIVE = 'Five'
    SIX = 'Six'
    SEVEN = 'Seven'
    EIGHT = 'Eight'
    NINE = 'Nine'
    TEN = 'Ten'
    JACK = 'Jack'
    QUEEN = 'Queen'
    KING = 'King'

    @classmethod
    def from_str(cls, s: str) -> Rank | None:
        for rank in Rank:
            if rank.value == s:
                return rank

        return None

    def __repr__(self):
        return self.value


class Suit(StrEnum):
    CLUBS = 'Clubs'
    DIAMONDS = 'Diamonds'
    HEARTS = 'Hearts'
    SPADES = 'Spades'

    @classmethod
    def from_str(cls, s: str) -> Suit | None:
        for suit in Suit:
            if suit.value == s:
                return suit

        return None

    def __repr__(self):
        return self.value


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def __str__(self):
        return f'{self.rank} of {self.suit}'

    @classmethod
    def standard_cards(cls) -> list[Card]:
        return [Card(rank, suit) for rank in Rank for suit in Suit]


class ParseState(IntEnum):
    """
    FSM/DFA (CS 133) or Moore machine (CS 20) representing parsing state.
    Static constraint of FSM should be fine since line sequences are also static.

    The state REGULAR_ROUND means the parser is expecting the line "Round n".
    """
    REGULAR_ROUND = auto()
    REGULAR_PLAYER_1_LABEL = auto()
    REGULAR_PLAYER_1_CARD = auto()
    REGULAR_PLAYER_2_LABEL = auto()
    REGULAR_PLAYER_2_CARD = auto()
    ROUND_WINNER = auto()
    COMMENCING_WAR = auto()
    WAR_ROUND = auto()
    WAR_PLAYER_1_LABEL = auto()
    WAR_PLAYER_1_CARD_UP = auto()
    WAR_PLAYER_1_CARD_DOWN = auto()
    WAR_PLAYER_2_LABEL = auto()
    WAR_PLAYER_2_CARD_UP = auto()
    WAR_PLAYER_2_CARD_DOWN = auto()
    CONTINUING_WAR = auto()
    WINNER_PLAYER_1 = auto()
    WINNER_PLAYER_2 = auto()
    DRAW = auto()
    NO_MORE_LINES = auto()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class WarState(StrEnum):
    # Can use `| None` instead of another enum value, but is more verbose annotation-wise
    NO_WAR = 'NO_WAR'
    WAR_START = 'WAR_START'
    WAR_ONGOING = 'WAR_ONGOING'
    WAR_END = 'WAR_END'


class GameEndState(StrEnum):
    PLAYER_1_WIN = 'PLAYER_1_WIN'
    PLAYER_2_WIN = 'PLAYER_2_WIN'
    DRAW = 'DRAW'


class Line:
    """
    Warning: Does not conform to LSP and OCP; OO approximation for algebraic data types (FP).
    Uses inheritance (OO) instead of type unions (not as OO) to enforce subtyping relations.
    """
    ...


@dataclass
class RoundLine(Line):
    round_number: int


@dataclass
class PlayerLabelLine(Line):
    player_number: int


@dataclass
class FaceUpCardLine(Line):
    rank: Rank
    suit: Suit


@dataclass
class FaceDownCardLine(Line):
    rank: Rank
    suit: Suit


@dataclass
class RoundWinnerLine(Line):
    player_number: int
    rank: Rank
    suit: Suit


@dataclass
class CommencingWarLine(Line):
    pass


@dataclass
class WarRoundLine(Line):
    round_number: int
    war_round_number: int


@dataclass
class ContinuingWarLine(Line):
    pass


@dataclass
class GameWinnerLine(Line):
    winner: int
    card_count: int


@dataclass
class DrawLine(Line):
    pass


@dataclass
class EmptyLine(Line):
    pass


@dataclass
class MalformedLine(Line):
    text: str
