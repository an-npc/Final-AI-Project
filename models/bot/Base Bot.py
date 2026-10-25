class BaseBot():
    # acts as the parent already passing the mandatory attributes and function of a bot to its children
    def __init__(self):
        """_note_
        bot should have access to its hand, know the rules
        """
        hand = [] # stores type card

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
    
    def add_card(self):
        """_note_
        adds card to bots hand
        """
        pass
