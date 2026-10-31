import sys, os
sys.path.append(os.path.abspath(".."))
from models.GameElements.Card import Card
from models.GameElements.Deck import Deck
from models.bot.BaseBot import BaseBot

class Game():
    """_note_
    runs the hand and enforces the rules, and each bot only decides what to do on its turn.
    """
    STAGES = ["preflop", "flop", "turn", "river", "showdown"]

    def __init__(self, players: list[BaseBot]):
        self.players = players        # list of bots
        self.deck = Deck()
        self.community_cards = []     # shared cards, up to 5
        self.pot = 0
        self.table_bet = 0            # highest bet this betting round
        self.stage = "preflop"
        self.folded = []              # players out of this hand

    def start_hand(self):
        """_note_
        shuffle, deal 2 cards to each player, post blinds
        """
        self.deck.shuffle()
        for player in self.players:
            player.add_card(self.deck.give_card())
            player.add_card(self.deck.give_card())

    def betting_round(self):
        """_note_
        ask each active player for an action 
        (fold, check, call, bet, or raise) 
        until the round ends
        """
        pass

    def next_stage(self):
        """_note_
        reset table_bet and each player's current_bet,
        deal shared cards (3 for flop, 1 for turn, 1 for river)
        """
        pass

    def showdown(self):
        """_note_
        find the best hand, pay the pot to the winner
        """
        pass
