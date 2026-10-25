class BaseBot():
    # acts as the parent already passing the mandatory attributes and function of a bot to its children
    def __init__(self):
        """_note_
        bot should have access to its hand, know the rules
        """
        self.hand = [] # stores type card

    def get_hand(self):
        """_note_
        returns list of cards currently in the bots hand
        """
        return self.hand

    def remove_card(self, card):
        """_note_
        removes the specified card from list of cards
        """
        self.hand.remove(card)

    def add_card(self, card):
        """_note_
        adds card to bots hand
        """
        self.hand.append(card)

    # actions
    def fold(self):
        """_note_
        forfeit hand and claim to the pot, throws away hand
        """
        pass

    def check(self):
        """_note_
        pass action to next player without placing bet
        allowed when no one has made a bet yet
        """

        pass

    def call(self):
        """_note_
        match the current active bet or raise
        """

        pass

    def bet(self):
        """_note_
        make the first wager of the betting round
        """

        pass

    def raise_bet(self):
        """_note_
        increase the size of a bet
        """

        pass

    def all_in(self):
        """_note_
        wager all of your remaining chips
        """

        pass
