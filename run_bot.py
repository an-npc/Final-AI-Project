"""_note_
connects a bot to the poker server and plays until stopped with Ctrl+C
run from the project folder:
    python run_bot.py
    python run_bot.py --id group-1 --name "Bot Group 1" --url ws://localhost:8000/ws
"""
import argparse
import asyncio
import json

import websockets

from models.bot.BaseBot import BaseBot


async def play(bot, my_id, name, url):
    """_note_
    joins the table, then answers every state snapshot where it is this bots turn
    """
    async with websockets.connect(url) as websocket:
        await websocket.send(json.dumps({"type": "join", "name": name, "player_id": my_id}))
        print(f"{name} connected to {url}")
        last_sent = None

        while True:
            message = json.loads(await websocket.recv())
            msg_type = message.get("type")

            if msg_type == "state":
                state = message["payload"]
                if state["current_turn"] != my_id:
                    continue  # server sends a snapshot after every change, most are not our turn

                bot.update_from_state(state, my_id)
                action, amount = bot.choose_action(state)
                last_sent = action
                await websocket.send(json.dumps({"type": "action", "action": action, "amount": amount}))
                print(f"[hand {state['hand_number']} {state['phase']}] hand={bot.get_hand()} chips={bot.get_chips()} -> {action} {amount or ''}")

            elif msg_type == "action_result":
                result = message["payload"]
                if not result["ok"]:
                    print("Rejected:", result["error"])
                    # still our turn after a rejected action, call is always legal so fall back to it once
                    if last_sent != "call":
                        last_sent = "call"
                        await websocket.send(json.dumps({"type": "action", "action": "call"}))

            elif msg_type == "error":
                print("Server error:", message["message"])


def main():
    parser = argparse.ArgumentParser(description="Connect a bot to the poker server.")
    parser.add_argument("--id", default="group-1", help="stable player_id, reconnecting with it keeps your seat")
    parser.add_argument("--name", default="Bot Group 1", help="name shown at the table")
    parser.add_argument("--url", default="ws://localhost:8000/ws", help="server websocket address")
    args = parser.parse_args()

    bot = BaseBot()
    try:
        asyncio.run(play(bot, args.id, args.name, args.url))
    except KeyboardInterrupt:
        print("\nBot stopped.")


if __name__ == "__main__":
    main()
