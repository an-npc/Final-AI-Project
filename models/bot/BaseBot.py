class BaseBot():
    # acts as the parent already passing the mandatory attributes and function of a bot to its children
    def __init__(self):
        """_note_
        bot should have access to its hand, know the rules
        """
        self.hand = [] # stores type card
        self.chips = 0
        self.current_bet = 0

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

    def get_chips(self):
        """_note_
        returns amount of chips currently in the bots hand
        """
        return self.chips

    def gain_chips(self, chips_awarded):
        """_note_
        adds chips earned to its overall chip amount
        """
        self.chips += chips_awarded

    def lose_chips(self, chips_lost):
        """_note_
        removes chips lost from its chip amount
        """
        self.chips -= chips_lost

    def place_bet(self, chips_bet):
        """_note_
        tracks what amount it is currently betting
        """
        self.current_bet = chips_bet

    def get_current_bet(self):
        """_note_
        returns what amount it is currently betting
        """
        return self.current_bet

    def reset_round(self):
        """_note_
        sets current_bet back to 0, should be called at the end of each round
        """
        self.current_bet = 0

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

    def call(self, table_bet):
        """_note_
        matches the current highest bet(table_bet) for the round
        table_bet determines how much the boy owes
        then returns how many chips it put in
        """

        amount_owed = table_bet - self.current_bet
        amount = min(amount_owed, self.chips)  # can't pay more than you have (all-in)

        self.chips -= amount
        self.current_bet += amount
        
        return amount

    def bet(self, bet_amount):
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
