from __future__ import annotations
from typing import Collection
import re

from project_types import Line, Rank, Suit, ParseState, WarState, GameEndState, \
    RoundLine, PlayerLabelLine, FaceUpCardLine, FaceDownCardLine, RoundWinnerLine, \
    CommencingWarLine, WarRoundLine, ContinuingWarLine, GameWinnerLine, DrawLine, EmptyLine, \
    MalformedLine


class LineParser:
    """
    Responsible for determining type of line parsed.

    Should probably be just a single function, but we want to stick to pure OOP.
    """

    @classmethod
    def default(cls) -> LineParser:
        return LineParser([1, 2], 52)

    def __init__(self, valid_player_numbers: Collection[int], max_cards: int):
        player_pattern_str = r'Player (?P<player_number>\d+)'
        card_pattern_str = r'(?P<rank>[A-Za-z]+) of (?P<suit>[A-Za-z]+)'
        round_pattern_str = r'Round (?P<round_number>\d+)'

        # f-strings are used even for str variables for each multiline syntax
        self._round_line_pattern = re.compile(f'^{round_pattern_str}$')
        self._player_label_line_pattern = re.compile(
            f'^{player_pattern_str}:$')
        self._face_up_card_line_pattern = re.compile(f'^- {card_pattern_str}$')
        self._face_down_card_line_pattern = re.compile(f'^- {card_pattern_str}'
                                                       r' \(face down\)$')
        self._round_winner_pattern = re.compile('^Round winner:'
                                                f' {player_pattern_str}'
                                                f' \\({card_pattern_str}\\)$')
        self._commencing_war_pattern = re.compile(r'^Commencing war\.\.\.$')
        self._war_round_line_pattern = re.compile(f'^{round_pattern_str}'
                                                  r', War (?P<war_number>\d+)$')
        self._continuing_war_pattern = re.compile(r'^Continuing war\.\.\.$')
        self._game_winner_line_pattern = re.compile(f'^{player_pattern_str}'
                                                    r' wins with (?P<card_count>\d+) cards in their deck$')
        self._draw_line_pattern = re.compile(r'^The game ended in a draw$')

        self._valid_player_numbers = set(valid_player_numbers)
        self._max_cards = max_cards

    def parse_line(self, line: str) -> Line:
        if '\n' in line:
            return MalformedLine(line)

        line = line.strip()

        if line == "":
            return EmptyLine()

        elif m := self._round_line_pattern.match(line):
            try:
                round_number = int(m['round_number'])
            except ValueError:
                pass
            else:
                return RoundLine(round_number)

        elif m := self._player_label_line_pattern.match(line):
            try:
                player_number = int(m['player_number'])
            except ValueError:
                pass
            else:
                if player_number in self._valid_player_numbers:
                    return PlayerLabelLine(player_number)

        elif m := self._face_up_card_line_pattern.match(line):
            rank = Rank.from_str(m['rank'])
            suit = Suit.from_str(m['suit'])

            if rank is not None and suit is not None:
                return FaceUpCardLine(rank, suit)

        elif m := self._face_down_card_line_pattern.match(line):
            rank = Rank.from_str(m['rank'])
            suit = Suit.from_str(m['suit'])

            if rank is not None and suit is not None:
                return FaceDownCardLine(rank, suit)

        elif m := self._round_winner_pattern.match(line):
            try:
                player_number = int(m['player_number'])
            except ValueError:
                pass
            else:
                rank = Rank.from_str(m['rank'])
                suit = Suit.from_str(m['suit'])

                if player_number in self._valid_player_numbers \
                        and rank is not None \
                        and suit is not None:
                    return RoundWinnerLine(player_number, rank, suit)

        elif self._commencing_war_pattern.match(line):
            return CommencingWarLine()

        elif m := self._war_round_line_pattern.match(line):
            try:
                round_number = int(m['round_number'])
                war_number = int(m['war_number'])
            except ValueError:
                pass
            else:
                return WarRoundLine(
                    round_number,
                    war_number,
                )

        elif self._continuing_war_pattern.match(line):
            return ContinuingWarLine()

        elif m := self._game_winner_line_pattern.match(line):
            try:
                player_number = int(m['player_number'])
                card_count = int(m['card_count'])
            except ValueError:
                pass
            else:
                if player_number in self._valid_player_numbers \
                        and 0 <= card_count <= self._max_cards:
                    return GameWinnerLine(player_number, card_count)

        elif self._draw_line_pattern.match(line):
            return DrawLine()

        return MalformedLine(line)


class ParseStateMachine:
    """
    Responsible for determining next parsing state given current
    parsing state, type of line parsed, and war state.

    Does not check deck consistency. Accommodates only two-player games.
    """

    @classmethod
    def default(cls) -> ParseStateMachine:
        return ParseStateMachine(ParseState.REGULAR_ROUND)

    def __init__(self, initial_state: ParseState):
        self._state = initial_state

    @property
    def state(self) -> ParseState:
        return self._state

    def update_state(self, line_type: Line,
                     war_state: WarState,
                     game_end_state: GameEndState | None) -> ParseState | None:
        next_state = self.next_state(self._state, line_type, war_state, game_end_state)

        if next_state is not None:
            self._state = next_state

        return next_state

    def next_state(self,
                   state: ParseState,
                   line_type: Line,
                   war_state: WarState,
                   game_end_state: GameEndState | None) -> ParseState | None:
        if isinstance(line_type, EmptyLine):
            # Self-loop; empty lines are to be ignored
            return state
        elif game_end_state is not None:
            return self._next_state_game_end(state, line_type, game_end_state)
        else:
            return self._next_state_game_ongoing(state, line_type, war_state)

    def _next_state_game_end(self, state: ParseState, line_type: Line,
                             game_end_state: GameEndState) -> ParseState | None:
        match (state, line_type, game_end_state):
            case ParseState.REGULAR_ROUND, \
                    RoundLine(), \
                    GameEndState.PLAYER_1_WIN:
                return ParseState.WINNER_PLAYER_1

            case ParseState.REGULAR_ROUND, \
                    RoundLine(), \
                    GameEndState.PLAYER_2_WIN:
                return ParseState.WINNER_PLAYER_2

            case ParseState.REGULAR_ROUND, \
                    RoundLine(), \
                    GameEndState.DRAW:
                return ParseState.DRAW

            case ParseState.WAR_ROUND, \
                    WarRoundLine(), \
                    GameEndState.PLAYER_1_WIN:
                return ParseState.WINNER_PLAYER_1

            case ParseState.WAR_ROUND, \
                    WarRoundLine(), \
                    GameEndState.PLAYER_2_WIN:
                return ParseState.WINNER_PLAYER_2

            case ParseState.WAR_ROUND, \
                    WarRoundLine(), \
                    GameEndState.DRAW:
                return ParseState.DRAW

            case ParseState.WINNER_PLAYER_1, \
                    GameWinnerLine(), \
                    _:
                if line_type.winner == 1:
                    return ParseState.NO_MORE_LINES

            case ParseState.WINNER_PLAYER_2, \
                    GameWinnerLine(), \
                    _:
                if line_type.winner == 2:
                    return ParseState.NO_MORE_LINES

            case ParseState.DRAW, \
                    DrawLine(), \
                    _:
                return ParseState.NO_MORE_LINES

    def _next_state_game_ongoing(self,
                                   state: ParseState,
                                   line_type: Line,
                                   war_state: WarState) -> ParseState | None:
        match (state, line_type, war_state):
            case ParseState.REGULAR_ROUND, \
                    RoundLine(), \
                    WarState.NO_WAR:
                return ParseState.REGULAR_PLAYER_1_LABEL

            case ParseState.REGULAR_PLAYER_1_LABEL, \
                    PlayerLabelLine(), \
                    WarState.NO_WAR:
                if line_type.player_number == 1:
                    return ParseState.REGULAR_PLAYER_1_CARD

            case ParseState.REGULAR_PLAYER_1_CARD, \
                    FaceUpCardLine(), \
                    WarState.NO_WAR:
                return ParseState.REGULAR_PLAYER_2_LABEL

            case ParseState.REGULAR_PLAYER_2_LABEL, \
                    PlayerLabelLine(), \
                    WarState.NO_WAR:
                if line_type.player_number == 2:
                    return ParseState.REGULAR_PLAYER_2_CARD

            case ParseState.REGULAR_PLAYER_2_CARD, \
                    FaceUpCardLine(), \
                    WarState.NO_WAR:
                return ParseState.ROUND_WINNER

            case ParseState.REGULAR_PLAYER_2_CARD, \
                    FaceUpCardLine(), \
                    WarState.WAR_START:
                return ParseState.COMMENCING_WAR

            case ParseState.REGULAR_PLAYER_2_CARD, \
                    FaceUpCardLine(), \
                    WarState.WAR_ONGOING:
                return ParseState.CONTINUING_WAR

            case ParseState.REGULAR_PLAYER_2_CARD, \
                    FaceUpCardLine(), \
                    WarState.WAR_END:
                return ParseState.ROUND_WINNER

            case ParseState.ROUND_WINNER, \
                    RoundWinnerLine(), \
                    WarState.NO_WAR:
                if line_type.player_number in {1, 2}:
                    return ParseState.REGULAR_ROUND

            case ParseState.COMMENCING_WAR, \
                    CommencingWarLine(), \
                    WarState.WAR_ONGOING:
                return ParseState.WAR_ROUND

            case ParseState.WAR_ROUND, \
                    WarRoundLine(), \
                    WarState.WAR_ONGOING:
                return ParseState.WAR_PLAYER_1_LABEL

            case ParseState.WAR_PLAYER_1_LABEL, \
                    PlayerLabelLine(player_number), \
                    WarState.WAR_ONGOING:
                if player_number == 1:
                    return ParseState.WAR_PLAYER_1_CARD_UP

            case ParseState.WAR_PLAYER_1_CARD_UP, \
                    FaceUpCardLine(), \
                    WarState.WAR_ONGOING:
                return ParseState.WAR_PLAYER_1_CARD_DOWN

            case ParseState.WAR_PLAYER_1_CARD_DOWN, \
                    FaceDownCardLine(), \
                    WarState.WAR_ONGOING:
                return ParseState.WAR_PLAYER_2_LABEL

            case ParseState.WAR_PLAYER_2_LABEL, \
                    PlayerLabelLine(player_number), \
                    WarState.WAR_ONGOING:
                if player_number == 2:
                    return ParseState.WAR_PLAYER_2_CARD_UP

            case ParseState.WAR_PLAYER_2_CARD_UP, \
                    FaceUpCardLine(), \
                    WarState.WAR_ONGOING:
                return ParseState.WAR_PLAYER_2_CARD_DOWN

            case ParseState.WAR_PLAYER_2_CARD_DOWN, \
                    FaceDownCardLine(), \
                    WarState.WAR_ONGOING:
                return ParseState.CONTINUING_WAR

            case ParseState.WAR_PLAYER_2_CARD_DOWN, \
                    FaceDownCardLine(), \
                    WarState.WAR_END:
                return ParseState.ROUND_WINNER

            case ParseState.CONTINUING_WAR, \
                    ContinuingWarLine(), \
                    WarState.WAR_ONGOING:
                return ParseState.WAR_ROUND

            case _, :
                pass

        return None  # Explicit return to signal that returning None is intended behavior
