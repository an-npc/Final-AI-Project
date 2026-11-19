"""AI-generated: this test file was written by Claude (Claude Code) for Colton, 2026-11-12. See ai_log_colton.md.
Colton reported on 2026-11-12 that the DeucesCracked targets below are accurate (see ai_log_colton.md).

Tests for models/equity/equity.py (equityV1). Run from the project root: python -m pytest tests/test_equity.py -v

All Monte Carlo tests use a fixed seed, so they are deterministic: the same code gives the same numbers every run.
Tolerance is about +-1% at 10,000 trials (the 95% margin of error at 10k trials is about 1%)."""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  # project root

import pytest
from models.equity.equity import equityV1
from models.GameElements.Card import Card

TRIALS = 10000
TOL = 0.01
SEED = 1


def cards(text):
    """'AhKs' -> [Card('A','h'), Card('K','s')]. Empty string -> []."""
    return [Card(text[i], text[i + 1]) for i in range(0, len(text), 2)]


# ---------------------------------------------------------------- DeucesCracked exact preflop matchups
# Targets (win%, loss%) are from CLAUDE.local.md section 5. Colton reported them accurate on 2026-11-12.
# Source: https://www.deucescracked.com/blog/preflop-poker-equity-matchups-exact-data
# The remainder (100 - win - loss) is ties. Suits are chosen so the two hands share no suit unless noted.
MATCHUPS = [
    # id,           hero,   villain, hero win, villain win
    ("AA_vs_KK",    "AhAs", "KdKc",  0.8106, 0.1855),
    ("AA_vs_AKo",   "AhAs", "AdKc",  0.9195, 0.0680),
    ("22_vs_AKs",   "2c2d", "AhKh",  0.4960, 0.4977),
]


@pytest.mark.parametrize("name, hero, villain, hero_win, villain_win", MATCHUPS, ids=[m[0] for m in MATCHUPS])
def test_deuces_cracked_matchup(name, hero, villain, hero_win, villain_win):
    r = equityV1(cards(hero), [], 1, simulations=TRIALS, seed=SEED, opponent_hands=[cards(villain)])
    assert r["win"] == pytest.approx(hero_win, abs=TOL)
    assert r["loss"] == pytest.approx(villain_win, abs=TOL)


@pytest.mark.parametrize("name, hero, villain, hero_win, villain_win", MATCHUPS, ids=[m[0] for m in MATCHUPS])
def test_matchup_is_symmetric(name, hero, villain, hero_win, villain_win):
    """Swapping hero and villain must swap win and loss (checks nothing depends on seat order)."""
    r = equityV1(cards(villain), [], 1, simulations=TRIALS, seed=SEED, opponent_hands=[cards(hero)])
    assert r["win"] == pytest.approx(villain_win, abs=TOL)
    assert r["loss"] == pytest.approx(hero_win, abs=TOL)


def test_heads_up_equity_is_win_plus_half_tie():
    r = equityV1(cards("AhAs"), [], 1, simulations=TRIALS, seed=SEED, opponent_hands=[cards("KdKc")])
    assert r["equity"] == pytest.approx(r["win"] + r["tie"] / 2, abs=1e-9)
    assert r["win"] + r["loss"] + r["tie"] == pytest.approx(1.0)


# ---------------------------------------------------------------- sanity checks against random opponents
def test_aa_vs_one_random():
    r = equityV1(cards("AhAs"), [], 1, simulations=TRIALS, seed=SEED)
    assert r["equity"] == pytest.approx(0.85, abs=TOL)


def test_aa_vs_two_random():
    r = equityV1(cards("AhAs"), [], 2, simulations=TRIALS, seed=SEED)
    assert r["equity"] == pytest.approx(0.73, abs=TOL)


def test_equity_falls_as_opponents_are_added():
    equities = [equityV1(cards("AhKd"), [], n, simulations=5000, seed=SEED)["equity"] for n in (1, 2, 3, 4)]
    assert equities == sorted(equities, reverse=True)


def test_suited_beats_offsuit_same_ranks():
    suited = equityV1(cards("AhKh"), [], 1, simulations=TRIALS, seed=SEED)["equity"]
    offsuit = equityV1(cards("AhKd"), [], 1, simulations=TRIALS, seed=SEED)["equity"]
    assert suited > offsuit


# ---------------------------------------------------------------- made hands on the board
def test_nut_hand_on_river_is_100_percent():
    # hero has a royal flush (Ah Kh + Qh Jh Th); nobody can tie or beat it
    for opponents in (1, 3):
        r = equityV1(cards("AhKh"), cards("QhJhTh2c3d"), opponents, simulations=500, seed=SEED)
        assert r["equity"] == 1.0
        assert r["win"] == 1.0


def test_drawing_dead_on_river_is_zero():
    # hero 2c3d plays 'nothing' against an opponent holding the royal flush
    r = equityV1(cards("2c3d"), cards("QhJhTh9c8d"), 1, simulations=500, seed=SEED, opponent_hands=[cards("AhKh")])
    assert r["equity"] == 0.0
    assert r["loss"] == 1.0


@pytest.mark.parametrize("opponents", [1, 2, 3, 5])
def test_royal_flush_on_board_everyone_ties(opponents):
    # the board is the royal flush, so every player's best five cards are the board
    r = equityV1(cards("2c3d"), cards("TsJsQsKsAs"), opponents, simulations=1000, seed=SEED)
    assert r["equity"] == pytest.approx(1 / (opponents + 1))
    assert r["tie"] == 1.0


# ---------------------------------------------------------------- tie rules (poker rules where a mistake can pass unnoticed)
def test_three_way_tie_gives_one_third_not_one_half():
    # board is the wheel (A-2-3-4-5); nobody's hole cards play, so all three tie
    r = equityV1(cards("9c9d"), cards("As2d3h4c5s"), 2, simulations=100, seed=SEED,
                 opponent_hands=[cards("KcQc"), cards("JcTc")])
    assert r["equity"] == pytest.approx(1 / 3)
    assert r["tie"] == 1.0


def test_wheel_straight_is_a_valid_straight_and_the_lowest():
    # hero and villain both play the board wheel -> exact tie
    tie = equityV1(cards("9c9d"), cards("As2d3h4c5s"), 1, simulations=100, seed=SEED, opponent_hands=[cards("KcQc")])
    assert tie["equity"] == 0.5
    # a 6 makes 2-3-4-5-6, which beats the wheel
    lose = equityV1(cards("9c9d"), cards("As2d3h4c5s"), 1, simulations=100, seed=SEED, opponent_hands=[cards("6c7h")])
    assert lose["equity"] == 0.0
    # hero holding the 6 beats a villain who only has the wheel
    win = equityV1(cards("6c7h"), cards("As2d3h4c5s"), 1, simulations=100, seed=SEED, opponent_hands=[cards("KcQc")])
    assert win["equity"] == 1.0


def test_kicker_decides_not_a_tie():
    # both pair the board ace; hero has a K kicker, villain a Q kicker
    r = equityV1(cards("KcQd"), cards("AsAd7h4c2s"), 1, simulations=100, seed=SEED,
                 opponent_hands=[cards("Qh9d")])
    assert r["equity"] == 1.0


def test_split_pot_with_same_pair_and_same_kickers():
    # board has AA K Q J; both players play the board's best five (A A K Q J) -> tie
    r = equityV1(cards("2c3d"), cards("AsAdKhQcJs"), 1, simulations=100, seed=SEED, opponent_hands=[cards("4c5d")])
    assert r["equity"] == 0.5


# ---------------------------------------------------------------- output fields, seeding, time mode
def test_same_seed_gives_identical_result():
    a = equityV1(cards("AhKd"), cards("Qh7c2d"), 2, simulations=2000, seed=42)
    b = equityV1(cards("AhKd"), cards("Qh7c2d"), 2, simulations=2000, seed=42)
    a.pop("ms"); b.pop("ms")  # timing differs run to run
    assert a == b


def test_different_seeds_give_different_trial_streams():
    a = equityV1(cards("AhKd"), [], 2, simulations=2000, seed=1)["equity"]
    b = equityV1(cards("AhKd"), [], 2, simulations=2000, seed=2)["equity"]
    assert a != b


def test_result_fields_and_margin():
    r = equityV1(cards("AhAs"), [], 1, simulations=TRIALS, seed=SEED)
    assert set(r) == {"equity", "win", "loss", "tie", "margin", "trials", "ms"}
    assert r["trials"] == TRIALS
    assert 0 <= r["equity"] <= 1
    assert 0 < r["margin"] <= 0.98 / TRIALS ** 0.5 + 1e-9  # margin never exceeds the worst-case 0.98/sqrt(N)


def test_margin_covers_the_true_value():
    # AA vs KK equity = 0.8106 + 0.0039/2 = 0.8126 (from the unverified MATCHUPS targets above; the 0.8125 here is rounded)
    r = equityV1(cards("AhAs"), [], 1, simulations=TRIALS, seed=SEED, opponent_hands=[cards("KdKc")])
    assert abs(r["equity"] - 0.8125) <= r["margin"] * 1.5


def test_time_budget_mode_stops_near_the_budget():
    r = equityV1(cards("AhAs"), [], 1, seed=SEED, time_budget_ms=100)
    assert r["trials"] > 1
    assert 100 <= r["ms"] < 100 + 300  # generous slack for a slow or busy machine


def test_time_budget_ignores_simulations():
    r = equityV1(cards("AhAs"), [], 1, simulations=3, seed=SEED, time_budget_ms=50)
    assert r["trials"] > 3


# ---------------------------------------------------------------- known cards and the flop/turn
def test_flop_and_turn_inputs_work():
    for board in ("Qh7c2d", "Qh7c2d9s"):
        r = equityV1(cards("AhKd"), cards(board), 1, simulations=1000, seed=SEED)
        assert 0 < r["equity"] < 1


def test_known_opponent_counts_toward_players():
    # players=2 with one known hand: the second opponent is random. Must differ from heads-up.
    heads_up = equityV1(cards("AhAs"), [], 1, simulations=TRIALS, seed=SEED, opponent_hands=[cards("KdKc")])["equity"]
    three_way = equityV1(cards("AhAs"), [], 2, simulations=TRIALS, seed=SEED, opponent_hands=[cards("KdKc")])["equity"]
    assert three_way < heads_up


# ---------------------------------------------------------------- input validation
def test_duplicate_card_in_hand_and_table_raises():
    with pytest.raises(ValueError):
        equityV1(cards("AhKd"), cards("Ah7c2d"), 1, simulations=10)


def test_duplicate_card_in_opponent_hand_raises():
    with pytest.raises(ValueError):
        equityV1(cards("AhKd"), [], 1, simulations=10, opponent_hands=[cards("AhQc")])


@pytest.mark.parametrize("board", ["Qh", "Qh7c", "Qh7c2d9s3c4d"])
def test_bad_board_size_raises(board):
    with pytest.raises(ValueError):
        equityV1(cards("AhKd"), cards(board), 1, simulations=10)


def test_wrong_hand_size_raises():
    with pytest.raises(ValueError):
        equityV1(cards("Ah"), [], 1, simulations=10)


def test_too_many_known_opponents_raises():
    with pytest.raises(ValueError):
        equityV1(cards("AhAs"), [], 1, simulations=10, opponent_hands=[cards("KdKc"), cards("QdQc")])


def test_opponent_hand_must_have_two_cards():
    with pytest.raises(ValueError):
        equityV1(cards("AhAs"), [], 1, simulations=10, opponent_hands=[cards("Kd")])
