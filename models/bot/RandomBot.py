import random

from models.bot.BaseBot import BaseBot

class RandomBot(BaseBot):
    """_note_
    baseline bot that picks uniformly from the actions that are legal right now.
    raises use the all-in target because it is always a legal raise amount.
    """

    def choose_action(self, state) -> tuple[str, int]:
        """_note_
        returns a random legal action and amount
        """
        all_in_target = self.current_bet + self.chips
        passive = "check" if self.current_bet == self.table_bet(state) else "call"

        options = ["fold", passive]
        if self.can_raise(state):
            options.append("raise")

        action = random.choice(options)
        return action, all_in_target if action == "raise" else 0
