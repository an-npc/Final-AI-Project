import sys, os
sys.path.append(os.path.abspath(".."))
from phevaluator import Card
import random

RANKS = "23456789TJQKA"
SUITS = "cdhs"

class Deck():
    def __init__(self):
        self.deck = []
        self.count = 52
        # AI-generated: builds phevaluator Cards from 2-char strings like "Ah", "Td"
        for suit in SUITS:
            for rank in RANKS:
                self.deck.append(Card(rank + suit))
                
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
