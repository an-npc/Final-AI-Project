import random

from models.bot.BaseBot import BaseBot


class AllInBot(BaseBot):
    """_note_
    baseline bot that wagers all of its remaining chips whenever it can raise.
    when its stack cannot cover the current bet it calls, which is an all-in call.
    """

    def choose_action(self, state) -> tuple[str, int]:
        """_note_
        returns a raise to the bot's maximum total bet for the round,
        or a call when raising is not possible
        """
        highest_bet = max(player["bet"] for player in state["players"])
        all_in_target = self.current_bet + self.chips

        if all_in_target > highest_bet:
            return "raise", all_in_target
        return "call", 0


class RandomBot(BaseBot):
    """_note_
    baseline bot that picks uniformly from the actions that are legal right now.
    raises use the all-in target because it is always a legal raise amount.
    """

    def choose_action(self, state) -> tuple[str, int]:
        """_note_
        returns a random legal action and amount
        """
        highest_bet = max(player["bet"] for player in state["players"])
        all_in_target = self.current_bet + self.chips
        passive = "check" if self.current_bet == highest_bet else "call"

        options = ["fold", passive]
        if all_in_target > highest_bet:
            options.append("raise")

        action = random.choice(options)
        return action, all_in_target if action == "raise" else 0
