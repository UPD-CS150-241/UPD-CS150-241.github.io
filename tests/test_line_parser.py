import project_types
from project_types import Rank, Suit
from parser import LineParser


def make_face_up_card_line(rank_str: str, suit_str: str):
    rank = Rank.from_str(rank_str)
    suit = Suit.from_str(suit_str)

    if rank is None:
        raise RuntimeError(f'{rank_str} is not a valid rank')

    if suit is None:
        raise RuntimeError(f'{suit_str} is not a valid suit')

    return project_types.FaceUpCardLine(rank, suit)


def make_face_down_card_line(rank_str: str, suit_str: str):
    rank = Rank.from_str(rank_str)
    suit = Suit.from_str(suit_str)

    if rank is None:
        raise RuntimeError(f'{rank_str} is not a valid rank')

    if suit is None:
        raise RuntimeError(f'{suit_str} is not a valid suit')

    return project_types.FaceDownCardLine(rank, suit)


def make_round_winner_line(player_number: int, rank_str: str, suit_str: str):
    rank = Rank.from_str(rank_str)
    suit = Suit.from_str(suit_str)

    if rank is None:
        raise RuntimeError(f'{rank_str} is not a valid rank')

    if suit is None:
        raise RuntimeError(f'{suit_str} is not a valid suit')

    return project_types.RoundWinnerLine(player_number, rank, suit)


def test_round_line():
    test_cases = [
        ('Round 1', project_types.RoundLine(1)),
        ('Round 9', project_types.RoundLine(9)),
        ('Round 10', project_types.RoundLine(10)),
        ('Round 99', project_types.RoundLine(99)),
        ('Round 100', project_types.RoundLine(100)),
        ('Round 100000', project_types.RoundLine(100000)),
        ('Round #1', None),
        ('round 1', None),
        ('Round 1:', None),
    ]

    parser = LineParser.default()

    for inp, out in test_cases:
        out = project_types.MalformedLine(inp) if out is None else out

        assert parser.parse_line(inp) == out


def test_player_label_line():
    test_cases = [
        ('Player 1:', project_types.PlayerLabelLine(1)),
        ('Player 2:', project_types.PlayerLabelLine(2)),
        ('Player 3:', None),
        ('Player 1', None),
        ('Player #1', None),
        ('Player #1:', None),
        ('player 1:', None),
    ]

    parser = LineParser.default()

    for inp, out in test_cases:
        out = project_types.MalformedLine(inp) if out is None else out

        assert parser.parse_line(inp) == out


def test_face_up_card_line():
    test_cases = [
        ('- Ace of Clubs', make_face_up_card_line('Ace', 'Clubs')),
        ('- Two of Diamonds', make_face_up_card_line('Two', 'Diamonds')),
        ('- Three of Hearts', make_face_up_card_line('Three', 'Hearts')),
        ('- Four of Spades', make_face_up_card_line('Four', 'Spades')),
        ('- Five of Spades', make_face_up_card_line('Five', 'Spades')),
        ('- Six of Spades', make_face_up_card_line('Six', 'Spades')),
        ('- Seven of Spades', make_face_up_card_line('Seven', 'Spades')),
        ('- Eight of Spades', make_face_up_card_line('Eight', 'Spades')),
        ('- Nine of Spades', make_face_up_card_line('Nine', 'Spades')),
        ('- Ten of Spades', make_face_up_card_line('Ten', 'Spades')),
        ('- Jack of Spades', make_face_up_card_line('Jack', 'Spades')),
        ('- Queen of Spades', make_face_up_card_line('Queen', 'Spades')),
        ('- King of Spades', make_face_up_card_line('King', 'Spades')),
        ('King of Spades', None),
        ('- king of clubs', None),
        ('- King Clubs', None),
        ('- 8 of Clubs', None),
        ('- Ace of Heart', None),
        ('- Ace of Diamond', None),
        ('- Ace of Spade', None),
        ('- Ace of Club', None),
    ]

    parser = LineParser.default()

    for inp, out in test_cases:
        out = project_types.MalformedLine(inp) if out is None else out

        assert parser.parse_line(inp) == out


def test_face_down_card_line():
    test_cases = [
        ('- Ace of Clubs (face down)', make_face_down_card_line('Ace', 'Clubs')),
        ('- Two of Diamonds (face down)', make_face_down_card_line('Two', 'Diamonds')),
        ('- Three of Hearts (face down)', make_face_down_card_line('Three', 'Hearts')),
        ('- Four of Spades (face down)', make_face_down_card_line('Four', 'Spades')),
        ('- Five of Spades (face down)', make_face_down_card_line('Five', 'Spades')),
        ('- Six of Spades (face down)', make_face_down_card_line('Six', 'Spades')),
        ('- Seven of Spades (face down)', make_face_down_card_line('Seven', 'Spades')),
        ('- Eight of Spades (face down)', make_face_down_card_line('Eight', 'Spades')),
        ('- Nine of Spades (face down)', make_face_down_card_line('Nine', 'Spades')),
        ('- Ten of Spades (face down)', make_face_down_card_line('Ten', 'Spades')),
        ('- Jack of Spades (face down)', make_face_down_card_line('Jack', 'Spades')),
        ('- Queen of Spades (face down)', make_face_down_card_line('Queen', 'Spades')),
        ('- King of Spades (face down)', make_face_down_card_line('King', 'Spades')),
        ('King of Spades (face down)', None),
        ('- king of clubs (face down)', None),
        ('- King Clubs (face down)', None),
        ('- 8 of Clubs (face down)', None),
        ('- Ace of Heart (face down)', None),
        ('- Ace of Diamond (face down)', None),
        ('- Ace of Spade (face down)', None),
        ('- Ace of Club (face down)', None),
    ]

    parser = LineParser.default()

    for inp, out in test_cases:
        out = project_types.MalformedLine(inp) if out is None else out

        assert parser.parse_line(inp) == out


def test_round_winner_line():
    test_cases = [
        ('Round winner: Player 1 (Ace of Clubs)', make_round_winner_line(1, 'Ace', 'Clubs')),
        ('Round winner: Player 1 (Two of Diamonds)', make_round_winner_line(1, 'Two', 'Diamonds')),
        ('Round winner: Player 1 (Three of Hearts)', make_round_winner_line(1, 'Three', 'Hearts')),
        ('Round winner: Player 1 (Four of Spades)', make_round_winner_line(1, 'Four', 'Spades')),
        ('Round winner: Player 1 (Five of Spades)', make_round_winner_line(1, 'Five', 'Spades')),
        ('Round winner: Player 1 (Six of Spades)', make_round_winner_line(1, 'Six', 'Spades')),
        ('Round winner: Player 1 (Seven of Spades)', make_round_winner_line(1, 'Seven', 'Spades')),
        ('Round winner: Player 1 (Eight of Spades)', make_round_winner_line(1, 'Eight', 'Spades')),
        ('Round winner: Player 1 (Nine of Spades)', make_round_winner_line(1, 'Nine', 'Spades')),
        ('Round winner: Player 1 (Ten of Spades)', make_round_winner_line(1, 'Ten', 'Spades')),
        ('Round winner: Player 1 (Jack of Spades)', make_round_winner_line(1, 'Jack', 'Spades')),
        ('Round winner: Player 1 (Queen of Spades)', make_round_winner_line(1, 'Queen', 'Spades')),
        ('Round winner: Player 1 (King of Spades)', make_round_winner_line(1, 'King', 'Spades')),
        ('Round winner: Player 1', None),
        ('round winner: player 1', None),
        ('round winner: player 1 (Ace of Clubs)', None),
    ]

    parser = LineParser.default()

    for inp, out in test_cases:
        out = project_types.MalformedLine(inp) if out is None else out

        assert parser.parse_line(inp) == out


def test_commencing_war_line():
    test_cases = [
        ('Commencing war...', project_types.CommencingWarLine()),
        ('commencing war...', None),
        ('Commencing war', None),
    ]

    parser = LineParser.default()

    for inp, out in test_cases:
        out = project_types.MalformedLine(inp) if out is None else out

        assert parser.parse_line(inp) == out


def test_war_round_line():
    test_cases = [
        ('Round 1, War 1', project_types.WarRoundLine(1, 1)),
        ('Round 1, War 9', project_types.WarRoundLine(1, 9)),
        ('Round 1, War 10', project_types.WarRoundLine(1, 10)),
        ('Round 2, War 99', project_types.WarRoundLine(2, 99)),
        ('Round 10, War 100', project_types.WarRoundLine(10, 100)),
        ('Round 100000, War 200000', project_types.WarRoundLine(100000, 200000)),
        ('Round 1, War 300000', project_types.WarRoundLine(1, 300000)),
        ('Round #1, War #1', None),
        ('round 1, war 1', None),
        ('Round 1, War 1:', None),
        ('Round 1 War 1', None),
    ]

    parser = LineParser.default()

    for inp, out in test_cases:
        out = project_types.MalformedLine(inp) if out is None else out

        assert parser.parse_line(inp) == out


def test_continuing_war_line():
    test_cases = [
        ('Continuing war...', project_types.ContinuingWarLine()),
        ('continuing war...', None),
        ('Continuing war', None),
    ]

    parser = LineParser.default()

    for inp, out in test_cases:
        out = project_types.MalformedLine(inp) if out is None else out

        assert parser.parse_line(inp) == out


def test_game_winner():
    test_cases = [
        ('Player 1 wins with 0 cards in their deck', project_types.GameWinnerLine(1, 0)),
        ('Player 1 wins with 1 cards in their deck', project_types.GameWinnerLine(1, 1)),
        ('Player 1 wins with 2 cards in their deck', project_types.GameWinnerLine(1, 2)),
        ('Player 1 wins with 10 cards in their deck', project_types.GameWinnerLine(1, 10)),
        ('Player 1 wins with 52 cards in their deck', project_types.GameWinnerLine(1, 52)),
        ('Player 2 wins with 0 cards in their deck', project_types.GameWinnerLine(2, 0)),
        ('Player 2 wins with 1 cards in their deck', project_types.GameWinnerLine(2, 1)),
        ('Player 2 wins with 2 cards in their deck', project_types.GameWinnerLine(2, 2)),
        ('Player 2 wins with 10 cards in their deck', project_types.GameWinnerLine(2, 10)),
        ('Player 2 wins with 52 cards in their deck', project_types.GameWinnerLine(2, 52)),
        ('player 1 wins with 52 cards in their deck', None),
        ('player 2 wins with 52 cards in their deck', None),
        ('Player 3 wins with 52 cards in their deck', None),
    ]

    parser = LineParser.default()

    for inp, out in test_cases:
        out = project_types.MalformedLine(inp) if out is None else out

        assert parser.parse_line(inp) == out


def test_draw_line():
    test_cases = [
        ('The game ended in a draw', project_types.DrawLine()),
        ('the game ended in a draw', None),
        ('The game ended in a draw...', None),
        ('The game ended with a draw', None),
    ]

    parser = LineParser.default()

    for inp, out in test_cases:
        out = project_types.MalformedLine(inp) if out is None else out

        assert parser.parse_line(inp) == out


def test_empty_line():
    test_cases = [
        ('', project_types.EmptyLine()),
        (' ', project_types.EmptyLine()),
        (' '*10, project_types.EmptyLine()),
    ]

    parser = LineParser.default()

    for inp, out in test_cases:
        out = project_types.MalformedLine(inp) if out is None else out

        assert parser.parse_line(inp) == out
