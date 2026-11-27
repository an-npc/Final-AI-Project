from models.bot.BaseBot import BaseBot


class AllInBot(BaseBot):
    """_note_
    baseline bot that wagers all of its remaining chips whenever it can raise.
    when its stack cannot cover the current bet it calls, which is an all-in call.
    """

    def choose_action(self, state) -> tuple[str, int]:
        """_note_
        returns a raise to the bot's maximum total bet for the round,
        or a call (check when free) when raising is not possible
        """
        if self.can_raise(state):
            return "raise", self.current_bet + self.chips
        if self.table_bet(state) == self.current_bet:
            return "check", 0
        return "call", 0
