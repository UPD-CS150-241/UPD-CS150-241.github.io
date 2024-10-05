from __future__ import annotations
from typing import Sequence, Collection, Mapping
from dataclasses import dataclass

from parser import LineParser, ParseStateMachine
from project_types import PlayerId, Line, Rank, WarState, Card, ParseState, \
    RoundLine, FaceUpCardLine, FaceDownCardLine, RoundWinnerLine, \
    CommencingWarLine, WarRoundLine, ContinuingWarLine, GameWinnerLine, DrawLine, \
    MalformedLine, GameEndState


@dataclass(frozen=True)
class ValidationError:
    error: str


@dataclass(frozen=True)
class ValidationResult:
    line_number: int
    state: ParseState
    error: ValidationError | None


class CardGroupDeck:
    """
    This represents an ordered sequence of unordered sets of cards.
    """

    @classmethod
    def standard(cls):
        return CardGroupDeck(Card.standard_cards())

    def __init__(self, initial: Collection[Card]):
        self._card_groups: list[set[Card]] = []

        if initial:
            self._card_groups.append(set(initial))

    def __len__(self):
        return sum(len(group) for group in self._card_groups)

    def can_draw(self, card: Card):
        return self._card_groups and card in self._card_groups[0]

    def remove_if_present(self, card: Card):
        for i, card_set in enumerate(self._card_groups):
            if card in card_set:
                card_set.remove(card)

                if not card_set:
                    # Mutating list being iterated over here is safe
                    # since this is always the last iteration
                    self._card_groups.pop(i)

                return

    def add_set_to_bottom(self, cards: Collection[Card]):
        self._card_groups.append(set(cards))

    def __str__(self):
        return f'{self._card_groups}'

    def __repr__(self):
        return str(self)


class CardConsistencyValidator:
    """
    This manages drawing of cards from a restricted pool of possible
    card with the actual sequence of cards initially unknown.

    This ensures that the sequence of cards drawn by each player
    is consistent across draws.
    """

    @classmethod
    def default(cls) -> CardConsistencyValidator:
        return CardConsistencyValidator({
            PlayerId(1): (26, Card.standard_cards()),
            PlayerId(2): (26, Card.standard_cards()),
        })

    def __init__(self, initial: Mapping[PlayerId, tuple[int, Collection[Card]]]):
        self._owner: dict[Card, PlayerId] = {}
        self._cards_in_play: set[Card] = set()

        self._card_group_decks: dict[PlayerId, CardGroupDeck] = {
            player_id: CardGroupDeck(possible_draws)
            for player_id, (_, possible_draws) in initial.items()
        }

        self._actual_card_counts: dict[PlayerId, int] = {
            player_id: count for player_id, (count, _) in initial.items()
        }

    def get_player_cards_left(self) -> dict[PlayerId, int]:
        return dict(self._actual_card_counts.items())

    def card_played_by(self, card: Card, player_id: PlayerId) -> ValidationError | None:
        if (ret := self._validate_played_card_rules(card, player_id)):
            return ret

        if card in self._owner:
            del self._owner[card]

        self._cards_in_play.add(card)
        self._actual_card_counts[player_id] -= 1

        for player_id, card_group_deck in self._card_group_decks.items():
            card_group_deck.remove_if_present(card)

    def cards_in_play_taken_by(self, player_id: PlayerId) -> ValidationError | None:
        ret = self._cards_added_to_deck_bottom(self._cards_in_play, player_id)
        self._actual_card_counts[player_id] += len(self._cards_in_play)
        self._cards_in_play.clear()

        return ret

    def _cards_added_to_deck_bottom(self, cards: Collection[Card],
                                    player_id: PlayerId) -> ValidationError | None:
        if (ret := self._validate_cards_added_rules(cards, player_id)):
            return ret

        self._card_group_decks[player_id].add_set_to_bottom(cards)

    def _validate_cards_added_rules(self, cards: Collection[Card],
                                    player_id: PlayerId) -> ValidationError | None:
        for card in cards:
            if (ret := self._ensure_card_in_play(card, player_id)):
                return ret

    def _ensure_card_in_play(self, card: Card, player_id: PlayerId) -> ValidationError | None:
        if self._owner.get(card) is None and card not in self._cards_in_play:
            return ValidationError(f'{card} to be taken by Player {player_id} is not in play')

    def _validate_played_card_rules(self, card: Card, player_id: PlayerId) -> ValidationError | None:
        if (ret := self._ensure_card_not_duplicated(card, player_id)):
            return ret

        if (ret := self._ensure_card_in_deck(card, player_id)):
            return ret

        if (ret := self._ensure_card_not_in_play(card)):
            return ret

    def _ensure_card_not_duplicated(self, card: Card, player_id: PlayerId) -> ValidationError | None:
        owner = self._owner.get(card)

        if owner is not None and owner != player_id:
            return ValidationError(f'{card} is not in deck of Player {player_id}')

    def _ensure_card_in_deck(self, card: Card, player_id: PlayerId) -> ValidationError | None:
        if not self._card_group_decks[player_id].can_draw(card):
            return ValidationError(f'{card} is not in topmost card group of deck of Player {player_id}')

    def _ensure_card_not_in_play(self, card: Card) -> ValidationError | None:
        if card in self._cards_in_play:
            return ValidationError(f'{card} is already in play')


class CardComparer:
    @classmethod
    def default(cls) -> CardComparer:
        return CardComparer([PlayerId(1), PlayerId(2)])

    def __init__(self, player_ids: list[PlayerId]):
        self._player_ids = player_ids
        self.reset_played_cards()

    def reset_played_cards(self):
        self._played_cards: dict[PlayerId, Card] = {}

    def face_up_card_played_by(self, card: Card, player_id: PlayerId) -> ValidationError | None:
        if card_in_play := self._played_cards.get(player_id):
            return ValidationError(f'Player {player_id} tried to play face up card {card},'
                                   f' but already has face up card {card_in_play} in play')

        self._played_cards[player_id] = card

    def get_current_face_up_card(self, player_id: PlayerId) -> Card | None:
        return self._played_cards.get(player_id)

    # FIXME: Non-`None` union isn't very OO
    def determine_winners(self) -> ValidationError | list[PlayerId]:
        ret: list[PlayerId] = []
        best_so_far: Card | None = None

        for player_id in self._player_ids:
            if (card := self._played_cards.get(player_id)) is None:
                return ValidationError(f'Player {player_id} still has no face up card')

            rank_order = [rank for rank in Rank]

            if best_so_far is None:
                best_so_far = card
                ret.append(player_id)
            else:
                self_rank = rank_order.index(card.rank)
                best_rank = rank_order.index(best_so_far.rank)

                if self_rank > best_rank:
                    ret.clear()

                if self_rank >= best_rank:
                    ret.append(player_id)

        return ret


class WarOutputValidator:
    @classmethod
    def default(cls):
        parser = LineParser.default()
        parse_manager = ParseStateMachine.default()
        card_validator = CardConsistencyValidator.default()
        card_comparer = CardComparer.default()

        return WarOutputValidator(parser, parse_manager, card_validator, card_comparer)

    def __init__(self,
                 parser: LineParser,
                 parse_manager: ParseStateMachine,
                 card_validator: CardConsistencyValidator,
                 card_comparer: CardComparer):
        self._parser = parser
        self._parse_manager = parse_manager
        self._card_validator = card_validator
        self._card_comparer = card_comparer

        self._round_number = 1
        self._line_number = 1
        self._war_round_number = 0
        self._war_state = WarState.NO_WAR
        self._game_end_state = None
        self._encountered_game_done_line = None

    @property
    def _state(self) -> ParseState:
        return self._parse_manager.state

    def validate_lines(self, lines: Sequence[str]) -> ValidationResult:
        for line in lines:
            if (error := self._validate_line(line)):
                return ValidationResult(self._line_number, self._state, error)

            self._line_number += 1

        if not self._encountered_game_done_line:
            cards_left = self._card_validator.get_player_cards_left()

            print(self._card_validator._card_group_decks)

            return ValidationResult(
                self._line_number,
                self._state,
                ValidationError('Game did not end;'
                                f' parse state {self._parse_manager.state},'
                                f' war state {self._war_state},'
                                f' game end state {self._game_end_state},'
                                f' and cards left {cards_left}')
            )

        return ValidationResult(self._line_number, self._state, None)

    def _get_players_left_after_n_draws(self, n: int) -> list[PlayerId]:
        ret: list[PlayerId] = []
        cards_left = self._card_validator.get_player_cards_left()

        for player_id, count in cards_left.items():
            if count > n:
                ret.append(player_id)

        return ret

    def _update_game_end_state_after_n_draws(self, n: int):
        players_left = self._get_players_left_after_n_draws(n)

        if len(players_left) == 0:
            self._game_end_state = GameEndState.DRAW

        elif len(players_left) == 1:
            if players_left[0] == PlayerId(1):
                self._game_end_state = GameEndState.PLAYER_1_WIN

                if players_left[0] == PlayerId(2):
                    self._game_end_state = GameEndState.PLAYER_2_WIN

    def _validate_line(self, line_str: str) -> ValidationError | None:
        line = self._parser.parse_line(line_str)

        # FIXME: `match`ing based on type is more FP than OOP
        match line:
            case RoundLine(round_number):
                if self._round_number != round_number:
                    return ValidationError(
                        f'Round number should be {self._round_number};'
                        f' found line with round number {round_number}'
                    )

                self._update_game_end_state_after_n_draws(0)

            case WarRoundLine(round_number, war_round_number):
                if self._round_number != round_number:
                    return ValidationError(
                        f'Round number should be {self._round_number};'
                        f' found line with round number {round_number}'
                    )

                if self._war_round_number != war_round_number:
                    return ValidationError(
                        f'War round number should be {self._war_round_number};'
                        f' found line with war round number {war_round_number}'
                    )

                self._update_game_end_state_after_n_draws(2)

            case FaceUpCardLine(rank, suit) | FaceDownCardLine(rank, suit):
                card = Card(rank, suit)
                current_player = self._get_player_to_play()

                if current_player is None:
                    return ValidationError(f'Cannot play {card}; no card can be played yet')

                if (error := self._card_validator.card_played_by(card, current_player)):
                    return error

                # FIXME: `isinstance` is not very OO in retrospect
                if isinstance(line, FaceUpCardLine):
                    if (error := self._card_comparer.face_up_card_played_by(
                            card, current_player)):
                        return error

                match (self._war_state, line):
                    # Comparison should only happen on face down card during war
                    case (WarState.NO_WAR, FaceUpCardLine()) \
                            | (WarState.WAR_ONGOING, FaceDownCardLine()):
                        match result := self._card_comparer.determine_winners():
                            case ValidationError():
                                # Ignore error; still waiting for cards to be played
                                pass

                            case _:
                                if len(result) > 1:
                                    if self._war_state == WarState.NO_WAR:
                                        self._war_state = WarState.WAR_START
                                    else:
                                        self._war_state = WarState.WAR_ONGOING
                                else:
                                    if self._war_state == WarState.WAR_ONGOING:
                                        self._war_state = WarState.WAR_END
                                    else:
                                        self._war_state = WarState.NO_WAR
                    case _:
                        pass

            case RoundWinnerLine(player_number, rank, suit):
                self._round_number += 1

                # FIXME: `match`ing based on type is more FP than OOP
                match result := self._card_comparer.determine_winners():
                    case ValidationError():
                        return result

                    case _:
                        if len(result) > 1:
                            return ValidationError(
                                f'Multiple winners ({result}),'
                                f' but line says winner is {player_number}'
                            )

                        winning_player = result[0]

                        if winning_player != player_number:
                            return ValidationError(
                                f'Player {winning_player} won;'
                                f' line says Player {player_number}'
                            )

                        correct_card = self._card_comparer.get_current_face_up_card(
                            winning_player)
                        card = Card(rank, suit)

                        if card != correct_card:
                            return ValidationError(
                                f'Player {winning_player} won with {correct_card};'
                                f' line says Player {winning_player} won with {card}'
                            )

                        if (error := self._card_validator.cards_in_play_taken_by(
                                PlayerId(player_number))):
                            return error

                        self._card_comparer.reset_played_cards()
                        self._war_state = WarState.NO_WAR

            case CommencingWarLine() | ContinuingWarLine():
                match result := self._card_comparer.determine_winners():
                    case ValidationError():
                        return result

                    case _:
                        verb = 'commence' if isinstance(line, CommencingWarLine) \
                            else 'continue'

                        if len(result) == 1:
                            return ValidationError(
                                f'Single winner ({result}),'
                                f' but line says war is to {verb}'
                            )

                        # FIXME: `isinstance` is not very OO in retrospect
                        if isinstance(line, CommencingWarLine):
                            self._war_round_number = 1
                        else:
                            self._war_round_number += 1

                        self._war_state = WarState.WAR_ONGOING
                        self._card_comparer.reset_played_cards()

            case GameWinnerLine() | DrawLine():
                self._encountered_game_done_line = True

            case MalformedLine(line_str):
                return ValidationError(f'Encountered malformed line: {line_str}')

            case _:
                pass

        if self._parse_manager.update_state(line, self._war_state,
                                            self._game_end_state) is None:
            cards_left = self._card_validator.get_player_cards_left()

            return ValidationError(f'Unexpected line {line}'
                                   f' for parse state {self._parse_manager.state}'
                                   f' with war state {self._war_state},'
                                   f' game end state {self._game_end_state},'
                                   f' and cards left {cards_left}')

    def _get_player_to_play(self) -> PlayerId | None:
        if self._state in {
            ParseState.REGULAR_PLAYER_1_CARD,
            ParseState.WAR_PLAYER_1_CARD_UP,
            ParseState.WAR_PLAYER_1_CARD_DOWN,
        }:
            return PlayerId(1)

        elif self._state in {
            ParseState.REGULAR_PLAYER_2_CARD,
            ParseState.WAR_PLAYER_2_CARD_UP,
            ParseState.WAR_PLAYER_2_CARD_DOWN,
        }:
            return PlayerId(2)

        else:
            return None

    def parse_lines(self, lines: Sequence[str]) -> list[Line | None]:
        return [self.parse_line(line) for line in lines]

    def parse_line(self, line: str) -> Line | None:
        return self._parser.parse_line(line)
