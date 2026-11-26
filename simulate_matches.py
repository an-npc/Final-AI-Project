"""_note_
AI-generated (Claude Code): plays MelBot against the other bots offline, using the server's own rules engine
(ai-poker-server-master/app/engine.py), so no server or websockets are needed.

each table is MelBot + 4 opponents (the tournament size). stacks are reset to 1000 before every hand, so every
hand is an independent trial. a hand is a WIN for MelBot if it ends with more chips than it started, a LOSS if
fewer, and a PUSH if even (e.g. it folded before putting anything in).

run from the project folder:
    python simulate_matches.py            # 10000 hands per table
    python simulate_matches.py --hands 500
"""
import argparse
import os
import random
import sys
import time

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai-poker-server-master"))
from app.engine import PokerEngine

from models.bot.AllInBot import AllInBot
from models.bot.BaseBot import BaseBot
from models.bot.MelBot import MelBot
from models.bot.RandomBot import RandomBot

STACK = 1000

TABLES = {
    "vs 4 BaseBots (check/call)": [BaseBot] * 4,
    "vs 4 RandomBots": [RandomBot] * 4,
    "vs 4 AllInBots": [AllInBot] * 4,
    "vs mixed (Base, Random, AllIn, Random)": [BaseBot, RandomBot, AllInBot, RandomBot],
}


def play_hand(engine, bots):
    """_note_
    plays one hand to the end, returns how many actions were rejected by the engine
    """
    for player in engine.players.values():
        player.stack = STACK
    engine.start_hand()
    rejected = 0
    while engine.phase not in ("WAITING", "SHOWDOWN") and engine.current_turn:
        pid = engine.current_turn
        state = engine.snapshot(pid)
        bots[pid].update_from_state(state, pid)
        action, amount = bots[pid].choose_action(state)
        if not engine.place_action(pid, action, amount)["ok"]:
            rejected += 1
            engine.place_action(pid, "call", 0)  # same fallback as run_bot.py
    if engine.phase == "SHOWDOWN":
        engine.finalize_showdown()
    return rejected


def run_table(opponent_classes, hands):
    engine = PokerEngine(starting_stack=STACK, small_blind=10, big_blind=20)
    bots = {"mel": MelBot()}
    engine.add_player("mel", "Mel Bot")
    for i, cls in enumerate(opponent_classes):
        pid = f"{cls.__name__}-{i}"
        bots[pid] = cls()
        engine.add_player(pid, pid)

    wins = losses = pushes = rejected = net = 0
    for _ in range(hands):
        rejected += play_hand(engine, bots)
        result = engine.players["mel"].stack - STACK
        net += result
        if result > 0:
            wins += 1
        elif result < 0:
            losses += 1
        else:
            pushes += 1
    return {"wins": wins, "losses": losses, "pushes": pushes, "net": net, "rejected": rejected}


def main():
    parser = argparse.ArgumentParser(description="Simulate MelBot against the other bots.")
    parser.add_argument("--hands", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    random.seed(args.seed)  # the engine's deck and RandomBot both use the global random

    print(f"{'table':40} {'wins':>6} {'losses':>7} {'pushes':>7} {'W/L':>6} {'chips/hand':>11} {'rejected':>9}")
    for name, opponents in TABLES.items():
        start = time.perf_counter()
        r = run_table(opponents, args.hands)
        ratio = r["wins"] / r["losses"] if r["losses"] else float("inf")
        print(f"{name:40} {r['wins']:6} {r['losses']:7} {r['pushes']:7} {ratio:6.2f} "
              f"{r['net'] / args.hands:11.1f} {r['rejected']:9}   ({time.perf_counter() - start:.0f}s)")


if __name__ == "__main__":
    main()
