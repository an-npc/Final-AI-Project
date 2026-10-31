import sys, os
sys.path.append(os.path.abspath(".."))
from models.card.Card import Card
import random

class Deck():
    def __init__(self):
        self.deck = []
        self.count = 52
        for suit in range(4):
            for rank in range(13):
                curr_suit = 'X' # acts as a error in case it isnt initialized properly
                match suit:
                    case 0:  # Ace
                        curr_suit = "A"
                    case 1: # Club
                        curr_suit = 'C'
                    case 2: # Heart
                        curr_suit = 'H'
                    case 3: #Diamond
                        curr_suit = 'D'
                # Aces are 1, Jacks are 11, Queens are 12, Kings are 13
                self.deck.append(Card(rank+1, curr_suit))
                
    def get_count(self):
        return self.count
    
    def get_deck(self):
        """_note_
        return the decks current order
        """
        return self.deck

    def shuffle(self):
        """_note_
        shuffles the deck
        """
        random.shuffle(self.deck)
        return self.deck

    def give_card(self):
        """_note_
        pops card from top of the deck and returns it
        """
        self.count = self.count - 1
        return self.deck.pop()

    # def __str__(self):
    #     return ", ".join(str(card) for card in self.deck)
