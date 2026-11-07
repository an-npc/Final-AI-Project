from models.GameElements.Card import Card

class BaseBot():
    # acts as the parent already passing the mandatory attributes and function of a bot to its children
    def __init__(self):
        """_note_
        bot should have access to its hand, know the rules
        """
        self.hand = [] # stores type card
        self.chips = 0
        self.current_bet = 0
        self.is_out = False # is checked by Game to determine skips or plays

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
        forfeit hand and claim to the pot including what you've already bet
        """
        self.hand = []
        self.is_out = True


    def check(self, table_bet):
        """_note_
        pass action to next player without placing bet
        allowed when no one has made a bet yet
        """
        print("Action has been checked")


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

    def raise_bet(self,table_bet,bet_amount):
        """_note_
        increase the size of a bet
        """
        if (self.chips != 0):
            self.chips -= bet_amount
            return bet_amount
        print('Chips are 0, Cannot Bet')

    def all_in(self,table_bet):
        """_note_
        wager all of your remaining chips
        """
        amount = self.chips
        self.chips = 0

        return amount

    # server
    def update_from_state(self, state, my_id):
        """_note_
        copies this bot's hand, chips, and current_bet from a server state snapshot
        the server is the source of truth, so this runs before every decision
        """
        me = next(p for p in state["players"] if p["id"] == my_id)
        # server ranks are 2-14 (14 = Ace), suits are full names like "spades"
        self.hand = [Card(c["rank"], c["suit"][0].upper()) for c in me["hole_cards"]]
        self.chips = me["stack"]
        self.current_bet = me["bet"]
        self.is_out = me["folded"]

    def choose_action(self, state):
        """_note_
        decides what to do on this bot's turn, returns action and amount
        for "raise", amount is the bots total bet for the round, not the extra chips
        child bots override this with their own strategy, default is check or call
        """
        table_bet = max(p["bet"] for p in state["players"])
        if table_bet == self.current_bet:
            return "check", 0
        return "call", 0