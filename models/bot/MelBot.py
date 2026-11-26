from models.bot.BaseBot import BaseBot, server_card
from models.equity.buckets import lookup_equity


class MelBot(BaseBot):
    """_note_
    AI-generated (Claude Code): equity bot that reads the lookup tables.
    preflop it uses preflop_equity.json, on the flop / turn / river it uses the bucket tables
    (flop_equity.json, turn_equity.json, river_equity.json), all through lookup_equity().

    strategy, every turn:
      1. equity = Pr(win | hand or bucket, opponents still in the hand)
      2. strong (equity well above a fair share of the pot) -> raise
      3. otherwise check if it's free, call if equity beats the pot odds, else fold
    """

    MAX_TABLE_OPPONENTS = 4  # the tables cover 1-4 opponents; more than that is treated as 4

    def opponents_in_hand(self, state):
        """_note_
        counts players other than this bot that still hold cards and haven't folded
        """
        count = sum(1 for p in state["players"]
                    if p["id"] != getattr(self, "id", None) and not p["folded"] and p["hole_cards"])
        return max(1, min(count, self.MAX_TABLE_OPPONENTS))

    def raise_threshold(self, opponents):
        """_note_
        equity needed to raise: 1.5x a fair share of the pot (1 / players), but never more than 0.65
        heads-up that is 0.65, against 4 opponents it is 0.30
        """
        return min(0.65, 1.5 / (opponents + 1))

    def choose_action(self, state) -> tuple[str, int]:
        board = [server_card(c) for c in state["community_cards"]]
        opponents = self.opponents_in_hand(state)
        equity = lookup_equity(self.hand, board, opponents)["equity"]

        highest_bet = max(p["bet"] for p in state["players"])
        to_call = highest_bet - self.current_bet
        max_target = self.current_bet + self.chips  # all-in, as a total bet for the round

        if equity >= self.raise_threshold(opponents) and max_target > highest_bet:
            # raising by at least the current bet is always a legal size (the last raise can't be bigger than it)
            size = max(state["big_blind"], highest_bet, int(0.75 * state["pot"]))
            return "raise", min(highest_bet + size, max_target)

        if to_call == 0:
            return "check", 0

        pot_odds = to_call / (state["pot"] + to_call)  # share of the final pot we would be paying
        if equity >= pot_odds:
            return "call", 0
        return "fold", 0
