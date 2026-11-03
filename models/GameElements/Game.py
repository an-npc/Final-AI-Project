import sys, os
from itertools import combinations
from collections import Counter
sys.path.append(os.path.abspath(".."))
from models.GameElements.Card import Card
from models.GameElements.Deck import Deck
from models.bot.BaseBot import BaseBot

class Game():
    """_note_
    runs the hand and enforces the rules, and each bot only decides what to do on its turn.
    """
    STAGES = ["preflop", "flop", "turn", "river", "showdown"]
    HAND_NAMES = ["High Card", "One Pair", "Two Pair", "Three of a Kind", "Straight", "Flush", "Full House", "Four of a Kind", "Straight Flush", "Royal Flush"]

    def __init__(self, players: list[BaseBot]):
        self.players = players        # list of bots
        self.deck = Deck()
        self.community_cards = []     # shared cards, up to 5
        self.pot = 0
        self.table_bet = 0            # highest bet this betting round
        self.stage = "preflop"
        self.folded = []              # players out of this hand

    def get_pot(self):
        """_note_
        returns the pot amount for round
        """
        return self.pot

    def get_table_bet(self):
        """_note_
        returns table bet aka the highest bet of the round
        """
        return self.table_bet

    def set_table_bet(self, new_bet):
        """_note_
        is set when a player makes a new bet
        """
        self.table_bet = max(self.table_bet, new_bet)
    
    def start_hand(self):
        """_note_
        shuffle, deal 2 cards to each player, post blinds
        """
        self.deck.shuffle()

        # deals two cards to each player, this is done in the preflop phase
        for player in self.players:
            player.add_card(self.deck.give_card())
            player.add_card(self.deck.give_card())

        # adds give cards to the community cards list
        for i in range(5):
            self.community_cards.append(self.deck.give_card())

    def betting_round(self):
        """_note_
        ask each active player for an action 
        (fold, check, call, bet, or raise) 
        until the round ends
        """
        pass

    def next_stage(self,stage):
        """_note_
        reset table_bet and each player's current_bet,
        deal shared cards (3 for flop, 1 for turn, 1 for river)
        """

        match stage:
            case "preflop":
                print("preflop")
                self.start_hand()
            case "flop":
                print("flop: revealing three cards")
                for index in range(3):
                    for player in self.players:
                        player.add_card(self.community_cards[index])
            case "turn":
                print("turn: revealing penultimate card")
                for player in self.players:
                    player.add_card(self.community_cards[3])
            case "river":
                print("river: revealing final card")
                for player in self.players:
                    player.add_card(self.community_cards[4])
            case "showdown":
                print("showdown")
                self.showdown()
    
    

    def showdown(self):
        """_note_
        find the best hand, pay the pot to the winner
        """
        hands = []
        for player in self.players:
            hands.append(player.get_hand())
        sorted_hands = self.sort_hands(hands_list=hands)
        # retrive the greatest hand from the list
        best_hand = sorted_hands[0]

    def sort_hands(self, hands_list):
        """_note_
        sorts the best hands in order from greatest to least
        """
        return sorted(hands_list, key=lambda hand: self.determine_hand(hand)[0], reverse=True)

    def determine_hand(self, hand):
        """_note_
        determines the hand type using the player's hand plus the community cards,
        returns (score, hand_name) where score is a tuple that can be compared
        directly, higher score = better hand
        """
        cards = hand + self.community_cards

        # tries every 5 card combo and keeps the best one
        best_score = None
        for combo in combinations(cards, 5):
            score = self.score_five(combo)
            if best_score is None or score > best_score:
                best_score = score

        return best_score, self.HAND_NAMES[best_score[0]]

    def score_five(self, cards):
        """_note_
        scores exactly 5 cards as (category, tiebreakers...)
        category goes from 0 (high card) to 9 (royal flush)
        """
        # Aces are stored as 1 but count high, so treat them as 14
        ranks = sorted((14 if int(card.get_rank()) == 1 else int(card.get_rank()) for card in cards), reverse=True)
        suits = [card.get_suit() for card in cards]

        is_flush = len(set(suits)) == 1

        # straight check, including the A-2-3-4-5 straight where the Ace plays low
        unique_ranks = sorted(set(ranks), reverse=True)
        straight_high = None
        if len(unique_ranks) == 5:
            if unique_ranks[0] - unique_ranks[4] == 4:
                straight_high = unique_ranks[0]
            elif unique_ranks == [14, 5, 4, 3, 2]:
                straight_high = 5

        # group ranks by how many times they appear, biggest groups first then highest rank
        counts = Counter(ranks)
        groups = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)
        group_ranks = [rank for rank, count in groups]
        group_sizes = [count for rank, count in groups]

        if straight_high == 14 and is_flush:
            return (9, straight_high)          # royal flush
        if straight_high and is_flush:
            return (8, straight_high)          # straight flush
        if group_sizes[0] == 4:
            return (7, *group_ranks)           # four of a kind
        if group_sizes == [3, 2]:
            return (6, *group_ranks)           # full house
        if is_flush:
            return (5, *ranks)                 # flush
        if straight_high:
            return (4, straight_high)          # straight
        if group_sizes[0] == 3:
            return (3, *group_ranks)           # three of a kind
        if group_sizes[:2] == [2, 2]:
            return (2, *group_ranks)           # two pair
        if group_sizes[0] == 2:
            return (1, *group_ranks)           # one pair
        return (0, *ranks)                     # high card
