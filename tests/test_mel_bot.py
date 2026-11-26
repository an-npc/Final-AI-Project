"""AI-generated (Claude Code): tests for models/bot/MelBot.py.
Run from the project root: python -m pytest tests/test_mel_bot.py -v"""
import os
import random
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "ai-poker-server-master"))

import pytest
from app.engine import PokerEngine
from models.bot.MelBot import MelBot
from models.bot.RandomBot import RandomBot

SUITS = {"c": "clubs", "d": "diamonds", "h": "hearts", "s": "spades"}
RANKS = {r: i + 2 for i, r in enumerate("23456789TJQKA")}


def server_cards(text):
    """'AhKs' -> server card dicts, the format the bot receives over the websocket"""
    return [{"rank": RANKS[text[i]], "suit": SUITS[text[i + 1]]} for i in range(0, len(text), 2)]


def make_state(hole, board="", my_bet=0, my_stack=1000, opponent_bets=(0,), pot=None, folded=()):
    """builds a server-style state where it is MelBot's turn; folded lists indexes of opponents that folded"""
    players = [{"id": "mel", "stack": my_stack, "bet": my_bet, "folded": False, "hole_cards": server_cards(hole)}]
    for i, bet in enumerate(opponent_bets):
        players.append({"id": f"opp{i}", "stack": 1000, "bet": bet, "folded": i in folded,
                        "hole_cards": [{"rank": "?", "suit": "?"}] * 2})
    if pot is None:
        pot = my_bet + sum(opponent_bets)
    return {"players": players, "community_cards": server_cards(board), "pot": pot, "big_blind": 20,
            "current_turn": "mel"}


def decide(state):
    bot = MelBot()
    bot.update_from_state(state, "mel")
    return bot.choose_action(state)


def test_raises_pocket_aces_preflop():
    action, amount = decide(make_state("AhAs", my_bet=0, opponent_bets=(10, 20)))
    assert action == "raise" and amount > 20


def test_folds_seven_deuce_to_big_bet_multiway():
    action, _ = decide(make_state("7d2c", opponent_bets=(400, 400, 400, 400), pot=1630))
    assert action == "fold"


def test_checks_weak_hand_when_free():
    action, amount = decide(make_state("7d2c", board="AsKhQd", opponent_bets=(0, 0)))
    assert (action, amount) == ("check", 0)


def test_calls_small_bet_with_good_price():
    # 9-high open-ended straight draw facing a tiny bet into a big pot: pot odds ~5%, equity is much higher
    action, _ = decide(make_state("9s8s", board="JsTd2c", opponent_bets=(10,), pot=200))
    assert action == "call"


def test_raise_never_exceeds_stack():
    # normal raise would be to 40, but we only have 30 chips, so it's capped at all-in
    action, amount = decide(make_state("AhAs", my_bet=0, my_stack=30, opponent_bets=(20,)))
    assert action == "raise" and amount == 30


def test_calls_instead_of_raising_when_it_cannot_raise():
    # facing a bet bigger than our whole stack: only call (all-in) or fold are possible
    action, _ = decide(make_state("AhAs", my_stack=100, opponent_bets=(500,), pot=600))
    assert action == "call"


def test_counts_only_opponents_still_in_hand():
    bot = MelBot()
    state = make_state("AhAs", opponent_bets=(0, 0, 0, 0), folded=(0, 1, 2))
    bot.update_from_state(state, "mel")
    assert bot.opponents_in_hand(state) == 1


def test_caps_opponents_at_table_size():
    bot = MelBot()
    state = make_state("AhAs", opponent_bets=(0,) * 7)
    bot.update_from_state(state, "mel")
    assert bot.opponents_in_hand(state) == 4


def test_raise_threshold():
    bot = MelBot()
    assert bot.raise_threshold(1) == 0.65
    assert bot.raise_threshold(4) == pytest.approx(0.30)


def test_every_action_is_legal_in_real_engine():
    """plays 200 hands on the server's engine; the engine rejects illegal actions, so none may be rejected"""
    random.seed(0)
    engine = PokerEngine(starting_stack=1000, small_blind=10, big_blind=20)
    bots = {"mel": MelBot(), **{f"r{i}": RandomBot() for i in range(4)}}
    for pid in bots:
        engine.add_player(pid, pid)
    for _ in range(200):
        for p in engine.players.values():
            p.stack = 1000
        engine.start_hand()
        while engine.phase not in ("WAITING", "SHOWDOWN") and engine.current_turn:
            pid = engine.current_turn
            state = engine.snapshot(pid)
            bots[pid].update_from_state(state, pid)
            action, amount = bots[pid].choose_action(state)
            result = engine.place_action(pid, action, amount)
            if pid == "mel":
                assert result["ok"], (action, amount, result.get("error"))
            elif not result["ok"]:
                engine.place_action(pid, "call", 0)
        if engine.phase == "SHOWDOWN":
            engine.finalize_showdown()
