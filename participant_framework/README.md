# Bonanzha AI Agent Framework

A plug-and-play Python framework for building AI player agents for the **Bonanzha** card game hackathon.
Choose a strategy approach, implement a few key methods, and compete on the live scoreboard!

---

## Quick Start

```bash
# 1. Install dependencies
cd participant_framework
pip install -r requirements.txt

# 2. Run with the built-in heuristic (works out of the box)
python main.py --strategy heuristic --name MyTeam --game GAME1 --url http://localhost:5186

# 3. Or train a DQN agent offline, then play
python train.py --strategy dqn --episodes 50000
python main.py --strategy dqn --name MyTeam --game GAME1
```

## Directory Structure

```
participant_framework/
├── main.py                  # Entry point: join a live game
├── train.py                 # Entry point: train offline in the simulator
├── config.py                # Server URL, game ID, player name, etc.
├── requirements.txt         # Python dependencies
├── framework/               # Core framework (you usually don't need to edit these)
│   ├── api_client.py        #   REST API client for the game server
│   ├── card_config.py       #   Card types, exchange maps, utility functions
│   ├── game_objects.py      #   Data classes for game state
│   ├── player_agent.py      #   Agent loop: polls server → calls your strategy
│   ├── simulator.py         #   Offline Gymnasium environment for training
│   └── state_encoder.py     #   Converts game state → 75-element float vector
├── strategies/              # Strategy implementations (this is where YOU work!)
│   ├── base_strategy.py     #   BaseStrategy + ActionStrategy abstract classes
│   ├── random_strategy.py   #   Random (baseline, complete)
│   ├── heuristic_strategy.py#   Rule-based (complete, good starting point to study)
│   ├── dqn_strategy.py      #   Deep Q-Network (skeleton with TODOs)
│   ├── tabular_q_strategy.py#   Q-table lookup (skeleton with TODOs)
│   ├── genetic_strategy.py  #   Evolutionary weights (skeleton with TODOs)
│   └── statistical_strategy.py  # Card counting + probability (skeleton with TODOs)
├── training/                # Training infrastructure
│   ├── dqn_agent.py         #   Dueling DQN with prioritised replay
│   └── train_loop.py        #   Training loops for DQN, tabular Q, genetic
└── models/                  # Saved model checkpoints (created by training)
```

---

## Game Rules (Bonanzha)

Bonanzha is a card trading game based on Bohnanza. The goal is to **earn the most coins** by planting, growing, and harvesting fields of cards.

### Cards
There are **8 card types** with **104 total cards** in the deck:

| Card Type     | Count | Exchange Map (cards → coins)       |
|---------------|:-----:|-----------------------------------|
| Uranuceps     |   8   | 5→4, 4→3, 3→2, 2→1              |
| Merkubello    |   6   | 3→3, 2→2                         |
| Marshwaganda  |  10   | 6→4, 5→3, 4→2, 2→1              |
| Saturnjong    |  12   | 7→4, 6→3, 4→2, 2→1              |
| Jordflue      |  14   | 7→4, 6→3, 5→2, 3→1              |
| Jupitail      |  16   | 8→4, 7→3, 5→2, 3→1              |
| Plutos Mane   |  18   | 9→4, 8→3, 6→2, 3→1              |
| Venusvamp     |  20   | 10→4, 8→3, 6→2, 4→1             |

**Rarer cards** (Merkubello, Uranuceps) pay out faster but are harder to collect.
**Common cards** (Venusvamp, Plutos Mane) need more cards but there are more of them.

### Fields
Each player has **2 fields**. A field can only hold one card type at a time.

### Phases (each turn)
1. **Planting** — You MUST plant the first card from your hand onto a field. If neither field matches, you must harvest one first (losing cards that haven't reached a payout threshold).
2. **PlantingOptional** — You MAY plant the second card from your hand. Skip if it doesn't match.
3. **Trading** — Two cards are drawn face-up. The active player can offer trades to other players. All players can propose trades.
4. **TradePlanting** — All cards acquired through trading (and the drawn cards kept by the active player) must be planted.

### Harvesting
When you harvest a field, look up the card count in that type's exchange map. You earn the corresponding coins. Cards below the lowest threshold earn 0 coins.

### Game End
The game ends after the deck has been reshuffled **3 times**. After the final round, all fields are harvested. Highest total coins wins.

---

## Architecture: Two Strategy Interfaces

### Option A: `BaseStrategy` — Full Phase Control
Override individual methods for each game phase. Best for **rule-based**, **statistical**, and **hand-crafted** approaches.

```python
from strategies.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def planting_strategy(self, game_state, player, player_id):
        # Decide what to plant, which field, whether to harvest first
        ...

    def optional_planting_strategy(self, game_state, player, player_id):
        # Plant second card or skip
        ...

    def trading_strategy(self, game_state, player, player_id):
        # Propose trades or keep drawn cards
        ...

    def trade_planting_strategy(self, game_state, player, player_id):
        # Plant traded/drawn cards
        ...

    def optional_trading_strategy(self, game_state, player, player_id):
        # Respond to other players' trade offers (called when it's NOT your turn)
        ...
```

### Option B: `ActionStrategy` — Single Action Method
Override just one method: `select_action(observation, legal_actions, phase) → action_index`. The framework handles state encoding, legal action computation, and API calls. Best for **RL**, **Q-learning**, **evolutionary**, and other **ML** approaches.

```python
from strategies.base_strategy import ActionStrategy

class MyMLStrategy(ActionStrategy):
    def select_action(self, observation, legal_actions, phase):
        # observation: 75-element numpy array
        # legal_actions: list of valid action indices
        # phase: int (0=Planting, 1=Optional, 2=Trading, 3=TradePlanting)
        # Return: one of the legal_actions
        ...
```

The action encoding matches the simulator exactly, so **models trained offline work directly against the live server** with zero translation.

---

## Strategy Approaches

### 1. Random (baseline)
**File:** `strategies/random_strategy.py` — **Complete, no TODOs**

Picks a random legal action. Use this as the absolute baseline and to verify your setup works.

```bash
python main.py --strategy random --name TestBot --game GAME1
```

### 2. Heuristic (rule-based)
**File:** `strategies/heuristic_strategy.py` — **Complete, no TODOs**

Hand-crafted rules: plant on matching fields, harvest lowest-value fields, skip optional planting when no match, trade away unneeded cards. Study this to understand the game logic. A surprisingly strong baseline!

```bash
python main.py --strategy heuristic --name RuleBot --game GAME1
```

### 3. DQN (Deep Q-Network)
**File:** `strategies/dqn_strategy.py` — **Skeleton with TODOs**

A neural network learns to map game states to action values. Features:
- Dueling architecture (value + advantage streams)
- Prioritised experience replay
- Double DQN (reduced overestimation)
- Legal-action masking
- Curriculum learning (opponent upgrades during training)

```bash
# Train offline (no server needed)
python train.py --strategy dqn --episodes 50000

# Play with trained model
python main.py --strategy dqn --name DQNBot --game GAME1
```

**TODOs to improve:**
- Tune network size (hidden layers)
- Custom state encoding (add features the default misses)
- Reward shaping (bonus for reaching thresholds, penalties for wasted harvests)
- Epsilon decay schedule
- Training hyperparameters (learning rate, batch size, gamma)

### 4. Tabular Q-Learning
**File:** `strategies/tabular_q_strategy.py` — **Skeleton with TODOs**

Uses a lookup table instead of a neural network. Simpler, faster, and more interpretable.

```bash
python train.py --strategy tabular_q --episodes 30000
python main.py --strategy tabular_q --name QBot --game GAME1
```

**Key TODO:** `discretize_state()` — Convert the 75-dim float vector into a compact hashable key. This is critical: too many bins → table explodes, too few → loses information.

**Tips:**
- Start with 3-5 features (e.g., field types, field counts, phase)
- Bin continuous values into 3-5 buckets
- Consider phase-specific features
- Look at the Q-table size during training — aim for <100k states

### 5. Genetic / Evolutionary
**File:** `strategies/genetic_strategy.py` — **Skeleton with TODOs**

Evolves a weight vector that scores actions. No gradients needed.

```bash
python train.py --strategy genetic --episodes 200 --population 50
python main.py --strategy genetic --name EvoBot --game GAME1
```

**Key TODO:** `extract_features()` — Design features for (state, action) pairs. The score for each action is `dot(weights, features)`.

**Tips:**
- Boolean features work great (e.g., "does this match a field?")
- Normalize features to [0, 1]
- Start with 5-10 features, add more if needed
- Try different mutation rates and crossover strategies

### 6. Statistical / Bayesian
**File:** `strategies/statistical_strategy.py` — **Skeleton with TODOs**

Count visible cards to estimate what's left in the deck. Use probabilities to make decisions.

```bash
python main.py --strategy statistical --name StatBot --game GAME1
```

**Key TODO:** Implement probability-based decision logic using the provided card counting and probability utilities.

**Tips:**
- Use hypergeometric distribution for draw probabilities
- Track which cards have been seen (on fields, in hand, in trades)
- Estimate "hold value" of fields (expected future payoff from keeping them)
- This approach requires no training — it runs purely on game-time inference

---

## Strategy Comparison

| Approach     | Training? | Difficulty | Strengths                          | Weaknesses                        |
|-------------|:---------:|:----------:|------------------------------------|------------------------------------|
| Random       | No        | Trivial    | Zero effort baseline               | Terrible performance               |
| Heuristic    | No        | Easy       | Interpretable, surprisingly strong | Can't adapt, limited ceiling       |
| Statistical  | No        | Medium     | Principled, no training needed     | Complex probability calculations   |
| Tabular Q    | Yes       | Medium     | Simple, fast, interpretable        | State space explosion              |
| Genetic      | Yes       | Medium     | No gradients, easy to parallelize  | Needs good feature engineering     |
| DQN          | Yes       | Hard       | Powerful, handles raw state        | Slow to train, harder to debug     |

---

## State Vector Reference (75 features)

| Index     | Description                                      |
|-----------|--------------------------------------------------|
| 0–7       | Field 0: card type one-hot (8 types)             |
| 8         | Field 0: card count (normalized)                 |
| 9         | Field 0: harvest value (0–4, normalized)         |
| 10        | Field 0: distance to next threshold              |
| 11–18     | Field 1: card type one-hot (8 types)             |
| 19        | Field 1: card count (normalized)                 |
| 20        | Field 1: harvest value (0–4, normalized)         |
| 21        | Field 1: distance to next threshold              |
| 22–29     | Hand: card type counts (normalized)              |
| 30        | Hand: total size (normalized)                    |
| 31–38     | Drawn cards: type counts                         |
| 39–46     | Traded cards: type counts                        |
| 47        | Deck size (fraction of 104)                      |
| 48        | Round number (normalized)                        |
| 49        | Own coins (normalized)                           |
| 50–52     | Opponent coins (up to 3 opponents)               |
| 53–56     | Phase one-hot (Planting, Optional, Trading, TradePlanting) |
| 57–72     | Opponent fields (up to 2 opponents × 2 fields × 4 features) |
| 73        | Is last round flag                               |
| 74        | Deck urgency (depletion in last round)           |

## Action Space Reference

The `ActionStrategy` maps these action indices per phase:

### Phase 0 — Planting (mandatory)
| Action | Meaning |
|--------|---------|
| 0 | Plant on field 0 |
| 1 | Plant on field 1 |
| 2 | Harvest field 0, then plant |
| 3 | Harvest field 1, then plant |

### Phase 1 — PlantingOptional
| Action | Meaning |
|--------|---------|
| 0 | Plant on field 0 |
| 1 | Plant on field 1 |
| 2 | **Skip** (don't plant second card) |
| 3 | Harvest field 0, then plant |
| 4 | Harvest field 1, then plant |

### Phase 2 — Trading
| Action | Meaning |
|--------|---------|
| 0 | **Skip** (keep both drawn cards) |
| 1 | Offer drawn card 0 |
| 2 | Offer drawn card 1 |
| 3 | Offer both drawn cards |
| 4 | Offer drawn card 0 + specify a card from hand |
| 5 | Offer drawn card 1 + specify a card from hand |

### Phase 3 — TradePlanting
| Action | Meaning |
|--------|---------|
| 0 | Plant on field 0 |
| 1 | Plant on field 1 |
| 2 | Harvest field 0, then plant |
| 3 | Harvest field 1, then plant |

---

## Tips & Tricks

1. **Start with Heuristic** — Read `heuristic_strategy.py` to understand the game flow before trying ML approaches.

2. **Train offline first** — The simulator (`framework/simulator.py`) runs thousands of games per second. Train a model, then plug it into the live agent.

3. **Reward shaping matters** — The default reward is coin difference per step. Consider adding bonuses for:
   - Reaching a payout threshold
   - Planting on matching fields
   - Penalties for forced harvests below threshold

4. **Combine approaches** — Nothing stops you from using a trained model for planting decisions and heuristics for trading.

5. **Watch the scoreboard** — The GameScoreboard frontend shows live Elo ratings. Iterate fast.

6. **Card rarity is key** — Merkubello (6 cards) pays 3 coins for just 3 cards. Venusvamp (20 cards) needs 10 for 4 coins. Rare cards are high-risk/high-reward.

7. **Trading is underrated** — Good trade decisions can be the difference between winning and losing. Consider what opponents want.

8. **Late-game harvesting** — In the last round, harvest all valuable fields before the game auto-harvests them.

---

## FAQ

**Q: Can I mix strategies?** Yes! Create a strategy that uses DQN for planting and heuristics for trading.

**Q: Do I need a GPU?** No. DQN trains in CPU well enough for 50k episodes. GPU helps for longer training runs.

**Q: What's a good training target?** Start with beating the random baseline (avg ~3-4 coins), then aim to match heuristic (~6-8 coins), then exceed it.

**Q: Can I modify the framework files?** You can, but you usually don't need to. Focus on the strategy files.

**Q: How do I test without the server?** Use `train.py` — it runs games entirely in the local simulator.

---

Good luck, and may the best bean farmer win! 🌱
