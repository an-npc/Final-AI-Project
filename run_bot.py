"""_note_
connects a bot to the poker server and plays until stopped with Ctrl+C
run from the project folder:
    python run_bot.py
    python run_bot.py --id group-1 --name "Bot Group 1" --url ws://localhost:8000/ws
    python run_bot.py --bot all-in --id baseline-all-in --name "Baseline All-In"
    python run_bot.py --bot random --id baseline-random --name "Baseline Random"
    python run_bot.py --bot mel_bot --id mel-bot --name "Mel Bot"
"""
import argparse
import asyncio
import json

import websockets

from models.bot.BaseBot import BaseBot
from models.bot.AllInBot import AllInBot
from models.bot.MelBot import MelBot
from models.bot.RandomBot import RandomBot

BOTS = {
    "base": BaseBot,
    "all-in": AllInBot,
    "random": RandomBot,
    "mel_bot": MelBot,
}


def turn_key(state):
    """_note_
    identifies one decision point. the server re-sends the same snapshot (e.g. after a rejected
    action or someone joining), and those repeats must not be answered twice
    """
    return (state["hand_number"], state["phase"], state.get("current_bet"),
            tuple((p["id"], p["bet"], p["folded"], p["all_in"]) for p in state["players"]))


async def play(bot, my_id, name, url):
    """_note_
    joins the table, then answers every state snapshot where it is this bots turn
    the server folds (or checks) for us if we take longer than turn_timeout_seconds (config.toml)
    """
    async with websockets.connect(url) as websocket:
        await websocket.send(json.dumps({"type": "join", "name": name, "player_id": my_id}))
        print(f"{name} connected to {url}")
        pending = False      # an action is in flight, wait for its action_result
        last_turn = None     # turn_key of the last snapshot we answered
        fallback = None      # safe action for the current turn if ours is rejected

        while True:
            message = json.loads(await websocket.recv())
            msg_type = message.get("type")

            if msg_type == "state":
                state = message["payload"]
                if state["hand_number"] == 0:
                    pending, last_turn = False, None  # match restarted
                if pending or state["current_turn"] != my_id:
                    continue  # server sends a snapshot after every change, most are not our turn
                key = turn_key(state)
                if key == last_turn:
                    continue  # repeat of a turn we already answered

                action, amount = bot.act(state, my_id)
                me = next(p for p in state["players"] if p["id"] == my_id)
                fallback = "check" if me["bet"] == state.get("current_bet", me["bet"]) else "call"
                msg = {"type": "action", "action": action}
                if action in ("raise", "bet"):
                    msg["amount"] = amount  # the server rejects an amount on fold/check/call
                await websocket.send(json.dumps(msg))
                pending, last_turn = True, key
                print(f"[hand {state['hand_number']} {state['phase']}] hand={bot.get_hand()} chips={bot.get_chips()} -> {action} {amount or ''}")

            elif msg_type == "action_result":
                result = message["payload"]
                pending = False
                if not result["ok"]:
                    print("Rejected:", result["error"])
                    # still our turn after a rejected action, fall back once to check/call which is always legal
                    if fallback is not None:
                        await websocket.send(json.dumps({"type": "action", "action": fallback}))
                        pending, fallback = True, None

            elif msg_type == "error":
                print("Server error:", message["message"])
                pending = False


def main():
    parser = argparse.ArgumentParser(description="Connect a bot to the poker server.")
    parser.add_argument("--id", default="group-1", help="stable player_id, reconnecting with it keeps your seat")
    parser.add_argument("--name", default="Bot Group 1", help="name shown at the table")
    parser.add_argument("--url", default="ws://localhost:8000/ws", help="server websocket address")
    parser.add_argument("--bot", choices=BOTS, default="base", help="bot strategy to run")
    args = parser.parse_args()

    bot = BOTS[args.bot]()
    try:
        asyncio.run(play(bot, args.id, args.name, args.url))
    except KeyboardInterrupt:
        print("\nBot stopped.")


if __name__ == "__main__":
    main()
