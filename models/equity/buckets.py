"""AI-generated (Claude Code): bucketed equity tables for the flop, turn and river.

A full table of every (hole cards, board) is far too big after the flop (26M+ combos), so instead every situation
is sorted into a BUCKET that describes it in poker terms, and we store one win probability per bucket:

    bucket = (hand type,         e.g. "One Pair"         -- from phevaluator's rank
              detail,            e.g. "top pair"         -- how strong it is inside that type
              flush draw,        True / False            -- 4 cards of one suit, flop and turn only
              straight draw)     "open-ended" / "gutshot" / "none"

    stored value = Pr(win | bucket, opponents)  -- the same "probability" (pot share) as preflop_equity.json

Build the tables (a few minutes):   python models/equity/buckets.py
Use them in the bot:                lookup_equity(hand, table, opponents)

Showdown has no table: all cards are known, so phevaluator gives the exact winner and there is nothing to estimate.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))  # project root
import json
import math
import random
import time
from phevaluator import Card, evaluate_cards
from models.equity.equity import simulate, equityV1, deck, PREFLOP_PATH

HERE = os.path.dirname(os.path.abspath(__file__))
STAGES = {3: "flop", 4: "turn", 5: "river"}  # board size -> stage name
STAGE_PATHS = {name: os.path.join(HERE, f"{name}_equity.json") for name in STAGES.values()}

# phevaluator ranks run 1 (royal flush) .. 7462 (worst high card); each hand type owns one range.
# Royal flush is just the best straight flush, so it shares that bucket.
CATEGORIES = [(10, "Straight Flush"), (166, "Four of a Kind"), (322, "Full House"), (1599, "Flush"),
              (1609, "Straight"), (2467, "Three of a Kind"), (3325, "Two Pair"), (6185, "One Pair"),
              (7462, "High Card")]


def category(rank):
    for limit, name in CATEGORIES:
        if rank <= limit:
            return name


def _rank(card):  # 0 = deuce .. 12 = ace (card id = rank * 4 + suit)
    return Card.to_id(card) // 4


def _suit(card):
    return Card.to_id(card) % 4


def _detail(name, hole, board, my_rank):
    """How strong the hand is inside its type. Mostly: are OUR hole cards doing the work, or the board?"""
    h = [_rank(c) for c in hole]
    b = [_rank(c) for c in board]
    every = h + b
    count = {r: every.count(r) for r in set(every)}
    board_top = sorted(set(b), reverse=True)

    if name == "High Card":
        overs = sum(r > board_top[0] for r in h)
        return {0: "no overcards", 1: "1 overcard", 2: "2 overcards"}[overs]

    if name == "One Pair":
        p = next(r for r, n in count.items() if n == 2)
        if b.count(p) == 2:
            return "board pair"  # the pair is on the board, everyone has it
        if h[0] == h[1]:
            return "overpair" if p > board_top[0] else "underpair"
        if p == board_top[0]:
            return "top pair"
        if len(board_top) > 1 and p == board_top[1]:
            return "middle pair"
        return "low pair"

    if name == "Two Pair":
        board_pairs = sum(b.count(r) >= 2 for r in set(b))
        return {0: "both hole cards", 1: "one board pair"}.get(board_pairs, "board two pair")

    if name == "Three of a Kind":
        t = next(r for r, n in count.items() if n == 3)
        if h[0] == h[1] == t:
            return "set"  # pocket pair + one on the board: well hidden
        if b.count(t) == 3:
            return "board trips"
        return "trips"

    # Straight or better: on the river, check whether the 5 board cards alone already make this hand
    if len(board) == 5 and evaluate_cards(*map(str, board)) == my_rank:
        return "board plays"
    return "made"


def _flush_draw(hole, board):
    """4 cards of one suit, at least one of them ours."""
    suits = [_suit(c) for c in hole + board]
    return any(suits.count(s) == 4 and s in [_suit(c) for c in hole] for s in set(suits))


def _straight_draw(hole, board):
    """How many card ranks would complete a straight that uses at least one hole card: 2+ = open-ended, 1 = gutshot."""
    def values(cards):  # ace counts high (14) and low (1)
        v = set()
        for c in cards:
            r = _rank(c) + 2
            v.add(r)
            if r == 14:
                v.add(1)
        return v

    have, mine = values(hole + board), values(hole)
    completing = set()
    for low in range(1, 11):  # straights from A-5 up to T-A
        window = set(range(low, low + 5))
        missing = window - have
        if len(missing) == 1 and window & mine:
            completing.add(14 if missing == {1} else missing.pop())
    if len(completing) >= 2:
        return "open-ended"
    return "gutshot" if completing else "none"


def bucket(hole, board):
    """Returns the bucket for our 2 hole cards on a 3, 4 or 5 card board, as a dict."""
    my_rank = evaluate_cards(*map(str, hole + board))
    name = category(my_rank)
    weak = name not in ("Straight Flush", "Four of a Kind", "Full House", "Flush")
    drawing = len(board) < 5  # no cards left to come on the river
    return {
        "hand": name,
        "detail": _detail(name, hole, board, my_rank),
        "flush_draw": drawing and weak and _flush_draw(hole, board),
        "straight_draw": _straight_draw(hole, board) if drawing and weak and name != "Straight" else "none",
    }


def bucket_key(b):
    return f'{b["hand"]}|{b["detail"]}|{"flush draw" if b["flush_draw"] else "no flush draw"}|{b["straight_draw"]}'


def build_bucket_tables(opponent_counts=(1, 2, 3, 4), samples=200000, seed=1):
    """Writes flop_equity.json, turn_equity.json and river_equity.json.

    For each stage and opponent count we deal `samples` random situations (hole cards + board), find each one's
    bucket, play it out once with simulate(), and average the results per bucket. Common buckets get thousands
    of samples; rare ones (e.g. quads) get few, so every entry stores its sample count and margin of error."""
    rng = random.Random(seed)
    cards = list(deck.get_deck())
    for size, stage in STAGES.items():
        entries = []
        for opponents in opponent_counts:
            start = time.perf_counter()
            totals = {}  # key -> [bucket, sum of pot shares, samples]
            for _ in range(samples):
                rng.shuffle(cards)
                hole, board = cards[:2], cards[2:2 + size]
                b = bucket(hole, board)
                _, share = simulate(hole, board, opponents, rng)
                t = totals.setdefault(bucket_key(b), [b, 0.0, 0])
                t[1] += share
                t[2] += 1
            for key, (b, total, n) in totals.items():
                p = total / n
                entries.append({"bucket": key, **b, "opponents": opponents, "probability": round(p, 4),
                                "samples": n, "margin": round(1.96 * math.sqrt(p * (1 - p) / n), 4)})
            print(f"{stage}: {opponents} opponent(s), {len(totals)} buckets, {time.perf_counter() - start:.0f}s")
        entries.sort(key=lambda e: (e["opponents"], -e["probability"]))
        with open(STAGE_PATHS[stage], "w") as f:
            json.dump(entries, f, indent=2)


_tables = {}  # loaded once: stage -> {(key, opponents): entry}


def _table(stage):
    if stage not in _tables:
        path = PREFLOP_PATH if stage == "preflop" else STAGE_PATHS[stage]
        with open(path) as f:
            rows = json.load(f)
        if stage == "preflop":
            _tables[stage] = {(tuple(r["hand"]), r["opponents"]): r for r in rows}
        else:
            _tables[stage] = {(r["bucket"], r["opponents"]): r for r in rows}
    return _tables[stage]


def lookup_equity(hand, table, opponents, min_samples=300, fallback_ms=50):
    """Fast equity estimate for the bot. Returns {"equity", "source"}.

    preflop: exact hand from preflop_equity.json.  flop/turn/river: the bucket's probability.
    Falls back to live Monte Carlo (equityV1 with a time budget) if the situation isn't in a table
    or its bucket has fewer than min_samples samples."""
    stage = "preflop" if not table else STAGES[len(table)]
    if stage == "preflop":
        key = tuple(str(c) for c in sorted(hand, key=Card.to_id))
    else:
        key = bucket_key(bucket(hand, table))
    entry = _table(stage).get((key, opponents))
    if entry and entry.get("samples", min_samples) >= min_samples:
        return {"equity": entry["probability"], "source": f"{stage} table"}
    result = equityV1(hand, table, opponents, time_budget_ms=fallback_ms)
    return {"equity": result["equity"], "source": "monte carlo"}


if __name__ == "__main__":
    build_bucket_tables()
