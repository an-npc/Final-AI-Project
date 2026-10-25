class Card():
    def __init__(self, rank, suit):
        self.suit = suit
        self.rank = str(rank)
    def get_suit(self):
        return self.suit
    def get_rank(self):
        return self.rank
    def get_card(self):
        return "" + self.rank + self.suit
    def __str__(self):
        return "" + self.rank + self.suit
    def __repr__(self): # fixes the print list issue with deck
        return str(self)
