# Texas Hold Em Q/A with Claude

## what is the difference between pot and table_bet in simple terms?
In short: the **pot** is all the money in the middle, and **table_bet** is the price to stay in right now.

- **Pot:** every chip anyone has put in during the whole hand. It only ever goes up, and the winner takes all of it at the end.
- **table_bet:** the most any one player has put in during the **current betting round**. It resets to 0 at the start of each round (preflop, flop, turn, river).

### Example

Three players, one betting round:

| Action | table_bet | Pot |
|---|---|---|
| Round starts | 0 | 0 |
| Player A bets 50 | 50 | 50 |
| Player B calls (pays 50) | 50 | 100 |
| Player C calls (pays 50) | 50 | 150 |
| Next round starts (flop) | **0** (reset) | 150 (kept) |

All three players called, but table_bet stayed at 50. Calling matches the bet; it doesn't raise it. Only a bet or a raise increases table_bet. The pot grows with every chip anyone puts in.

### In your code

- `call(table_bet)` uses table_bet to work out how much the bot owes.
- The game loop adds whatever `call` returns to the pot: `pot += bot.call(table_bet)`.

The bot never needs to know the pot to call. It only needs table_bet.

## what is calling?
Calling means matching the **highest** bet anyone has made in this round, not just the previous player's. Most of the time the previous player has the highest bet, which is why it looks that way.

### When they differ

| Action | table_bet | Cost to call |
|---|---|---|
| A bets 50 | 50 | |
| B raises to 100 | 100 | |
| C calls | 100 | **100** (matches B, the highest) |
| A calls | 100 | **50** (A already put in 50, so A owes 50 more) |

A has to come back and pay more because B raised after A bet. A betting round only ends when everyone still in the hand has put in the same amount, or has folded or gone all-in.

### The rule in short

- **Call** = put in enough to bring your bet this round up to `table_bet`.
- **Cost** = `table_bet - what you've already put in this round`.

That's the line in your `call` method:

```python
amount_owed = table_bet - self.current_bet
```

Your `call` method already handles the case where A comes back and owes only 50, because it subtracts what the bot has already put in.

## when does a round end?
"Round" can mean two things in poker, and your code needs both: a **betting round** and a whole **hand**.

### A betting round ends when...

Everyone still in the hand has had at least one turn, and one of these is true:

1. **Everyone has matched `table_bet`.** Every remaining player has put in the same amount this round, or is all-in.
2. **Everyone checked.** No one bet, so `table_bet` stayed at 0.
3. **Only one player is left.** Everyone else folded, so that player wins the pot right away and the hand is over.

A raise reopens the action: everyone who already acted has to respond again. That's why A had to come back and call in the last example.

### A hand has up to 4 betting rounds

| Betting round | What happens first |
|---|---|
| **Preflop** | Each player is dealt 2 private cards |
| **Flop** | 3 shared cards are placed face up on the table |
| **Turn** | 1 more shared card is added |
| **River** | 1 last shared card is added |

After the river's betting, the remaining players show their cards (the **showdown**). The best 5-card hand made from your 2 cards plus the 5 shared cards wins the pot.

The hand ends after the showdown, or earlier if everyone but one player folds. Then a new hand starts with a fresh deck.

### What resets when

| | End of a betting round | End of a hand |
|---|---|---|
| `table_bet` | reset to 0 | reset to 0 |
| bot's `current_bet` | reset to 0 (`reset_round`) | reset to 0 |
| pot | **kept** | paid to the winner, then 0 |
| bot's hand (cards) | kept | cleared |
| bot's chips | kept | kept (plus winnings) |

Your `reset_round` should run at the end of every **betting round**, not only at the end of the hand. Its docstring says "end of each round", so you might reword it to "end of each betting round" to make that clear.

One preflop detail you'll need later: two players are forced to put chips in before any cards are dealt (the **blinds**). So preflop starts with `table_bet` already above 0. I can explain blinds when you get to building the game loop.


## what happens in these stages? "preflop", "flop", "turn", "river", "showdown"
Each stage deals some cards (except showdown) and then has a round of betting. A hand can end early at any stage if everyone but one player folds; that player wins the pot without showing their cards.

### 1. Preflop
- **Blinds:** the two players to the left of the dealer post forced bets. The **small blind** is usually half the minimum bet, and the **big blind** is the full minimum bet. This makes sure there's always something in the pot to play for.
- **Deal:** each player gets 2 private cards (hole cards).
- **Betting:** starts with the player to the left of the big blind. Because the blinds count as a bet, players must **call, raise, or fold**. They can't check, except the big blind, who can check if nobody raised.

### 2. Flop
- **Deal:** 3 community cards face up.
- **Betting:** starts with the first active player to the left of the dealer. Nobody has bet yet, so players can **check** or **bet**.

### 3. Turn
- **Deal:** 1 more community card, for 4 total.
- **Betting:** same as the flop. In real games the minimum bet often doubles from here on.

### 4. River
- **Deal:** the last community card, for 5 total.
- **Betting:** same as the flop. This is the last chance to bet.

### 5. Showdown
- **No cards dealt and no betting.** Everyone still in reveals their cards.
- **Winner:** each player's best 5-card hand is found from their 2 cards plus the 5 community cards, and the best hand wins the pot. Equal hands split it.

### How this maps to your `Game` class

| Stage | Method that does the work |
|---|---|
| Start of preflop | `start_hand()`: shuffle, deal 2 cards each, post blinds |
| Every stage except showdown | `betting_round()`: once per stage |
| Moving to the next stage | `next_stage()`: reset `table_bet` and each player's `current_bet`, then deal 3, 1, or 1 cards |
| Showdown | `showdown()`: `determine_hand` / `sort_hands`, pay the pot |

A full hand would roughly run like this:

```python
self.start_hand()
for stage in ["preflop", "flop", "turn", "river"]:
    if stage != "preflop":
        self.next_stage()      # deals 3, then 1, then 1
    self.betting_round()
    if only one player is left:
        give them the pot and stop
self.showdown()
```

## Connect to the Bot Server
Connection was successful, but two new methods has to be added to the base bot. 
Game will be used a server substitute for baseline testing.

### How it works
The server runs the whole game: it deals, enforces the rules, and manages the pot. After every change it sends each bot a snapshot of the table as JSON. On the bot's turn, the bot replies with an action: `fold`, `check`, `call` or `raise`.

So your own `Game` class isn't used when playing on the server. It's still useful for testing offline.

### What I added

- **[run_bot.py](run_bot.py)** (new): connects to the server, joins the table, and waits for snapshots. On your turn it asks the bot what to do and sends the answer. If the server rejects a move, it falls back to `call` once, as the server's README recommends.
- **[BaseBot.py](models/bot/BaseBot.py)**, two new methods at the bottom:
  - `update_from_state(state, my_id)` copies your cards, chips and `current_bet` from the snapshot into the bot. The server's numbers are the real ones, so this runs before every decision.
  - `choose_action(state)` returns something like `("call", 0)`. The default checks when nothing is owed and calls otherwise. **This is where your strategy goes.** Write a child class that overrides it.

### Running it

1. Start the server (first terminal):
   ```
   cd ai-poker-server-master
   ..\.venv\Scripts\python -m uvicorn app.server:app --port 8000
   ```
2. Start your bot (second terminal, from the project folder):
   ```
   .venv\Scripts\python run_bot.py --id group-1 --name "Bot Group 1"
   ```
3. Add opponents to practice against: `.venv\Scripts\python ai-poker-server-master\scripts\demo_bots.py --count 2`
4. Open http://localhost:8000 and press **Start**.

For the real tournament, pass the professor's address with `--url ws://<their-server>:8000/ws`. Keep the same `--id` every time: reconnecting with it gets your seat and chips back.

### Things to know

- **Virtual environment:** I created `.venv` in the project folder and installed the server's requirements into it. Plain `python` doesn't have `websockets` installed, so use `.venv\Scripts\python`. The folder ignores itself in git.
- **Raise amount:** the server's `raise` amount is your **total** bet for the round, not the extra chips. To raise to 60 when you've already put in 20, send `("raise", 60)`.
- **Card format:** cards from the server use ranks 2–14 (Ace = 14) and suits S/H/D/C. Your `Deck` uses Ace = 1 and labels spades as `"A"`, so the hand-ranking code in `Game` may need adjusting before your strategy uses it on server cards.
- **Not committed yet:** `ai-poker-server-master/` and `run_bot.py` are untracked, and the `BaseBot.py` change is uncommitted.

## Equity
[equity.py](models/equity/equity.py) estimates **equity**, which is the chance your hand wins (or its share of the pot) against opponents. It does this with a **Monte Carlo simulation**. [`simulate`](models/equity/equity.py#L14) deals random opponent hands and the rest of the board, scores everyone with **phevaluator**, and returns a win, loss, or tie share. [`equityV1`](models/equity/equity.py#L59) repeats that many times, up to **10000 simulations**, and averages the results. It also supports a **seed** for reproducibility, known **opponent_hands**, and a **time_budget_ms** cap.

The point is to give your bot a numeric basis for its decisions. The **random and all-in baselines** from your earlier commits ignore hand strength. A smarter bot can compare its equity against the pot odds to decide whether to fold, call, or raise. It also lets you measure any later bot against those baselines.

## PhEvaluator Python Library
Used to determine how good of a hand the players hand. 
Scaled from 1 (best) to 7462 (worst)


## Update Local Card Object to PhEvaluator's Card
**Command**: update the equity.py to create a json file named preflop_equity.json. the json will have the structure of { { “hand” : ["4c", "4h”, "4s", , "9c", "9d"], probability” : 0.8 }, { “hand” : ["3c", "3h”, "3s", , "9c", "9d"],probability” : 0.3 }} sort the hand before inserting into the json file by using.

**Claude Response**: Every `from models.GameElements.Card import Card` in the project now imports `from phevaluator import Card`. All **37 tests** in `test_equity.py` pass.

The import swap alone would have broken things, because phevaluator's **Card** takes a single string like `Card("Ah")`, not `Card(rank, suit)`. It also has no `RANKS`, `SUITS`, `get_rank()` or `get_suit()`. So I also updated the code that used those:

- **[Deck.py](models/GameElements/Deck.py):** the rank and suit strings now live in the file itself, and each card is built as `Card(rank + suit)`.
- **[Game.py](models/GameElements/Game.py#L135-L136):** `score_five` now gets rank as `id_ // 4 + 2` (2 to 14) and suit as `id_ % 4`, using the **card ID** formula from the earlier `to_id` discussion.
- **[BaseBot.py](models/bot/BaseBot.py#L126):** server cards like `{rank: 14, suit: "spades"}` are converted to `Card("As")`.
- **[equity.py](models/equity/equity.py) and [test_equity.py](tests/test_equity.py#L21-L23):** both now use `Card("Ah")` and `Card(text[i:i+2])`.

I spot-checked a royal flush, a wheel straight, the 52-card deck and the server-card conversion, and all came out right. To run the tests I installed **pytest** into Python 3.14, since it wasn't there.

Two things are left for you:

- [Card.py](models/GameElements/Card.py) is now unused, but I left it in place. Let me know if I should delete it.
- Your notebook still has `Card(2,'H')`, which will error with phevaluator's Card. Change it to `Card("2h")`.


## Implementing the Lookup Tables for the Poker Stages
**Command** update the equity.py to create a json file named preflop_equity.json. the json will have the structure of { { “hand” : ["4c", "4h”, "4s", "9c", "9d"], "probability” : 0.8 }, { “hand” : ["3c", "3h”, "3s", "9c", "9d"], "probability” : 0.3 }, ... } sort the hand before inserting into the json file by using Card.to_id() which will return a rank from 0 to 51.

**Claude Response**
The full run finished, and [preflop_equity.json](models/equity/preflop_equity.json) now has **5,304 entries**: 1,326 hands for each of 1 to 4 **opponents**.

I spot-checked a few hands, and they match published preflop odds to within about 1%. That's the expected **margin** at 10,000 simulations.

| Hand | 1 opp | 2 opp | 3 opp | 4 opp |
|---|---|---|---|---|
| AA | 0.857 | 0.732 | 0.630 | 0.558 |
| AKs | 0.673 | 0.511 | 0.422 | 0.356 |
| 72o | 0.346 | 0.197 | 0.136 | 0.104 |

Equity drops as **opponents** are added, so the opponents field matters. Against your 4 bots, even AA wins only about 56% of the time.

To look up a hand during live play, sort the bot's two cards with `Card.to_id`, then match `hand` and `opponents`. Loading the file once into a dict keyed by `(card1, card2, opponents)` makes each lookup instant.