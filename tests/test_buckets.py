"""AI-generated (Claude Code): tests for models/equity/buckets.py bucket classification.
Run from the project root: python -m pytest tests/test_buckets.py -v"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  # project root

import pytest
from phevaluator import Card
from models.equity.buckets import bucket


def cards(text):
    return [Card(text[i:i + 2]) for i in range(0, len(text), 2)]


@pytest.mark.parametrize("hole, board, hand, detail, flush_draw, straight_draw", [
    ("AhKh", "Qh7h2c", "High Card", "2 overcards", True, "none"),       # nut flush draw
    ("9s8s", "JsTd2c", "High Card", "no overcards", False, "open-ended"),  # 8-9-T-J, needs 7 or Q
    ("9s8d", "Tc6d2s", "High Card", "no overcards", False, "gutshot"),     # needs a 7
    ("AsKd", "2c3d4s", "High Card", "2 overcards", False, "gutshot"),      # wheel draw, needs a 5
    ("AhKd", "Ac7d2s", "One Pair", "top pair", False, "none"),
    ("QsQd", "Jc7d2s", "One Pair", "overpair", False, "none"),
    ("5s5d", "Jc7d2s", "One Pair", "underpair", False, "none"),
    ("Ks7h", "KcJd7s", "Two Pair", "both hole cards", False, "none"),
    ("7s7d", "7c9d2s", "Three of a Kind", "set", False, "none"),
    ("2c3d", "AsKdQhJcTh", "Straight", "board plays", False, "none"),    # river: board is the hand
    ("AhKd", "Ac7d2s9c5h", "One Pair", "top pair", False, "none"),       # river: no draws
])
def test_bucket(hole, board, hand, detail, flush_draw, straight_draw):
    assert bucket(cards(hole), cards(board)) == {
        "hand": hand, "detail": detail, "flush_draw": flush_draw, "straight_draw": straight_draw}
