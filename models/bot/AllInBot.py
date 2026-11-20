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
