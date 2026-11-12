class Card():
    # AI-generated: replaced raw rank/suit storage with phevaluator format ("Ah", "Td") and added __eq__/__hash__.
    RANKS = "23456789TJQKA"
    SUITS = "cdhs"

    def __init__(self, rank, suit):
        rank_str = str(rank).strip().upper()
        if rank_str in ("1", "14"):      # Ace can arrive as 1 (old Deck) or 14 (server)
            rank_str = "A"
        elif rank_str.isdigit():         # numeric ranks: "2".."9", "10".."13"
            rank_str = self.RANKS[int(rank_str) - 2] if 2 <= int(rank_str) <= 13 else rank_str
        suit_str = str(suit).strip().lower()[:1]   # "S", "spades" -> "s"
        if rank_str not in self.RANKS or suit_str not in self.SUITS:
            raise ValueError(f"Invalid card: rank={rank!r}, suit={suit!r}")
        self.rank = rank_str
        self.suit = suit_str
    def get_suit(self):
        return self.suit
    def get_rank(self):
        return str(self.RANKS.index(self.rank) + 2)   # "2".."14", Ace = "14"
    def get_card(self):
        return "" + self.rank + self.suit
    def __str__(self):
        return "" + self.rank + self.suit
    def __repr__(self): # fixes the print list issue with deck
        return str(self)
    def __eq__(self, other):
        return isinstance(other, Card) and (self.rank, self.suit) == (other.rank, other.suit)
    def __hash__(self):
        return hash((self.rank, self.suit))
