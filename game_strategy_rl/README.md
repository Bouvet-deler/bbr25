# Bonanzha RL Agent

A Reinforcement Learning agent for the Bonanzha board game.

## Architecture

```
game_strategy_rl/
├── bonanzha_env.py       # Local game simulator (Gymnasium environment)
├── card_config.py        # Card type definitions mirroring server
├── state_encoder.py      # Encodes game state → fixed-size vector
├── dqn_agent.py          # DQN agent with per-phase action heads
├── rl_strategy.py        # GameStrategy-compatible wrapper (plays via API)
├── train.py              # Offline training loop using local simulator
├── main.py               # Entry point: run trained RL agent against server
├── models/               # Saved model checkpoints
└── requirements.txt      # Python dependencies
```

## Approach

### Why DQN?

The game has **discrete action spaces** per phase:
- **Planting**: choose field (2 fields) or harvest-then-plant
- **PlantingOptional**: plant on field / skip
- **Trading**: offer drawn cards / skip
- **TradePlanting**: choose field per card / harvest-then-plant

DQN with separate action heads per phase handles the variable action spaces
cleanly and trains efficiently with experience replay.

### State Representation

Fixed-size vector encoding:
- Per field (×2): card type one-hot (8), card count (1), harvest value (1), 
  next threshold distance (1) → 11 per field = 22
- Hand: type counts (8), hand size (1) → 9
- Drawn cards: type counts (8) → 8
- Global: deck size normalized (1), round normalized (1), coin count (1),
  opponent coin counts (4), phase one-hot (4) → 11
- Total: ~50 features

### Training

1. **Self-play** in the local simulator with 4 agents
2. **Experience replay** buffer with prioritized sampling
3. **Target network** with soft updates
4. **Curriculum**: start with random opponents, gradually use copies of best model

### Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Train the agent (offline, no server needed)
python train.py --episodes 50000

# Run trained agent against the live server
python main.py --model models/best.pt --game GAME1
```
