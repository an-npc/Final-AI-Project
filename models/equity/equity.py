import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))) # project root, works from any folder
import json
import math
import random
import time
from phevaluator import evaluate_cards  # lower score = better hand (1 = royal flush, 7462 = worst)
from models.GameElements.Card import Card
from models.GameElements.Deck import Deck

deck = Deck()

def simulate(hand, table, players, rng=random, opponent_hands=()):
    """Simulates a poker game for given hand and returns the equity of hand vs other player(s)

    Returns (result, share): result is 0 = won, 1 = lost, 2 = tied;
    share is our part of the pot (1 for a win, 0 for a loss, 1/k for a k-way tie).
    rng is the random source, so equityV1 can pass a seeded one (see seed there).
    opponent_hands: opponents whose 2 cards are already known; the other (players - len) get random cards."""
    hands = [list(h) for h in opponent_hands]
    hand = hand[:]
    table = table[:]

    known = table + hand # our own 7 cards, this is what gets scored
    dead = known + [c for h in hands for c in h] # every card that can't be dealt again
    remaining = [c for c in deck.get_deck() if c not in dead] #remove known cards from deck
    rng.shuffle(remaining) # shuffles our own copy with the seeded rng (Deck.shuffle uses the global random)

    #deal cards to the opponents whose hands we don't know
    for i in range(players - len(opponent_hands)):
        hn = [remaining.pop(), remaining.pop()] #deal 2 cards
        hands.append(hn)

    #flop, turn, river
    while len(table) < 5:
        card = remaining.pop()
        table.append(card)
        known.append(card)

    my_hand_rank = evaluate_cards(*map(str, known))

    opponent_ranks = []
    for opponent_hand in hands:
        opponent_known = table + opponent_hand
        opponent_ranks.append(evaluate_cards(*map(str, opponent_known)))
    best_opponent_rank = min(opponent_ranks, default=7463) # 7463 = worse than any real hand

    # compare once, after every opponent has been scored
    if best_opponent_rank < my_hand_rank:
        return 1, 0 #lost
    if best_opponent_rank == my_hand_rank:
        # tie scoring: the pot is split between us and every opponent with the same rank, so we get 1/k
        return 2, 1 / (1 + opponent_ranks.count(my_hand_rank)) #tied
    return 0, 1 #won

RESULTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "equity_results.json")

def equityV1(hand, table, players, simulations = 10000, seed = None, opponent_hands = None, time_budget_ms = None):
    """Calculates the equity of a hand vs opponents using Monte Carlo simulation

    hand: our 2 cards. table: 0, 3, 4 or 5 board cards. players: number of OPPONENTS.
    simulations: number of trials. time_budget_ms: if given, run trials until it runs out instead (simulations is ignored).
    seed: same seed + same inputs = same answer (use it in tests); None = different every run.
    opponent_hands: optional list of known opponent hands, e.g. [[Card, Card]] for AA vs a specific hand.
        They count toward players, the remaining opponents get random cards.

    Returns a dict:
      equity (0-1), win, loss, tie (fractions of trials), margin (95% margin of error on equity),
      trials (how many were actually run), ms (how long it took).
    margin = 1.96 * sqrt(p(1-p)/N) with p = equity; at most about 0.98/sqrt(N) (~1% at 10k trials). It is slightly
      pessimistic because ties give fractional shares, which vary less than the p(1-p) formula assumes.

    TIE SCORING (how we count ties, and why):
    - A k-way tie gives us 1/k of the pot (2-way = 0.5, 3-way = 0.33, ...), because the pot really is split that way.
    - Heads-up this equals win + tie/2. With 2+ opponents it does NOT: win + tie/2 would score a 3-way tie as 0.5
      instead of 0.33, overstating equity (most for hands that tie a lot, e.g. when the board plays).
    - So use the returned equity for pot-odds decisions, not win + tie/2.
    - The [win, loss, tie] fractions count any tie with the best opponent as a tie, whatever k is,
      so they can't be turned back into equity multiway. DeucesCracked numbers are heads-up, so they compare fine."""
    opponent_hands = opponent_hands or []
    all_cards = [str(c) for c in hand + table + [c for h in opponent_hands for c in h]]
    if len(hand) != 2 or len(table) not in (0, 3, 4, 5):
        raise ValueError("need 2 hole cards and a board of 0, 3, 4 or 5 cards")
    if len(opponent_hands) > players or any(len(h) != 2 for h in opponent_hands):
        raise ValueError("opponent_hands must be 2-card hands, no more than players")
    if len(set(all_cards)) != len(all_cards):
        raise ValueError("the same card appears twice in hand, table and opponent_hands")

    rng = random.Random(seed)
    distribution = [0, 0, 0] # wins, losses, ties
    equity_total = 0
    trials = 0
    start = time.perf_counter()
    while True:
        result, share = simulate(hand, table, players, rng, opponent_hands)
        distribution[result] += 1
        equity_total += share
        trials += 1
        if time_budget_ms is None:
            if trials >= simulations:
                break
        elif (time.perf_counter() - start) * 1000 >= time_budget_ms: # always runs at least 1 trial
            break
    ms = (time.perf_counter() - start) * 1000

    equity = equity_total / trials
    margin = 1.96 * math.sqrt(equity * (1 - equity) / trials)
    win, loss, tie = [x / trials for x in distribution]
    return {"equity": equity, "win": win, "loss": loss, "tie": tie, "margin": margin, "trials": trials, "ms": ms}

def save_result(hand, table, players, result, seed = None, opponent_hands = None, path = RESULTS_PATH):
    """Appends one equityV1 result, with the inputs that produced it, to a JSON file (a list of runs).

    Call it right after equityV1: save_result(hand, table, players, result, seed, opponent_hands).
    The file is created if it doesn't exist; an existing file that isn't a JSON list is never overwritten."""
    record = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hand": [str(c) for c in hand],
        "table": [str(c) for c in table],
        "opponents": players,
        "opponent_hands": [[str(c) for c in h] for h in (opponent_hands or [])],
        "seed": seed,
        **result,
    }
    runs = []
    if os.path.exists(path):
        with open(path) as f:
            runs = json.load(f) # raises if the file is corrupt, so we never silently wipe old results
        if not isinstance(runs, list):
            raise ValueError(f"{path} is not a JSON list, not overwriting it")
    runs.append(record)
    with open(path, "w") as f:
        json.dump(runs, f, indent=2)
    return record

if __name__ == "__main__":
    # example call: AA vs 1 random opponent, preflop. Run: python models/equity/equity.py
    hand = [Card("A", "h"), Card("A", "s")]
    table = []
    players = 1
    seed = 1
    result = equityV1(hand, table, players, simulations = 10000, seed = seed)
    print(result)
    save_result(hand, table, players, result, seed) # creates models/equity/equity_results.json on first call