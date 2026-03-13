# Concurrency Problem in Single-Process Multi-Player Client

## Problem Description

The current `main.py` implementation simulates all 4 players in a **single-threaded sequential loop**. This breaks the core game mechanics designed for concurrent player interaction.

## Current Architecture Issue

```python
while not game.is_game_over():
    game_state = game.get_game()
    current_player = game.get_current_player(game_state)
    
    # Only acts for the CURRENT player
    game.decide_next_move(game_state, current_player, player_id=current_player_id)
    sleep(10)  # Then sleeps for 10 seconds
```

### What Happens:
1. Loop fetches game state
2. Identifies **current player only**
3. Executes move for current player
4. **Sleeps for 10 seconds** (all players blocked!)
5. Repeats

### Why This Breaks the Game:

#### **Trading Phase is Impossible**
- Player1 (current) posts a trade offer
- Player2, Player3, Player4 **cannot respond** because the loop is sleeping
- Only Player1's thread is active during Player1's turn
- Other players never get a chance to call `accept_trade`

#### **Validation Rules Violated**
The server expects:
- Current player can **post** trades (`request-trade`)
- **Any player** can **accept** trades where current player is involved
- This requires **all players to be actively polling** during the Trading phase

## Required Architecture

### Multi-Threaded Solution

Each player needs their own thread continuously monitoring and acting:

```python
def player_agent(game, player_id, player_name):
    while not game.is_game_over():
        game_state = game.get_game(player_id=player_id)
        
        # Check if I'm the current player
        if game_state.current_player == player_name:
            # Execute my turn logic
            execute_turn_strategy(game_state, player_id)
        else:
            # I'm NOT current player, but can still act
            if game_state.current_phase == 'Trading':
                # Check for trade offers I can accept
                evaluate_and_accept_trades(game_state, player_id)
        
        sleep(1)  # Short poll interval

# Spawn 4 concurrent threads
threads = [
    Thread(target=player_agent, args=(game, p['playerId'], p['playerName']))
    for p in player_list
]
for t in threads:
    t.start()
```

### Key Requirements:
1. **All players poll continuously** (every 1-2 seconds)
2. **Current player** executes turn-based actions (plant, end-trading)
3. **Non-current players** respond to opportunities (accept trades)
4. **No global lock** that blocks all players during one player's turn

## Impact on Game Phases

| Phase | Current Player | Other Players |
|-------|---------------|---------------|
| **Planting** | Plants cards, ends phase | Wait (no actions available) |
| **Trading** | Posts trades, can accept others' trades | **Can accept current player's trades** |
| **TradePlanting** | Plants traded cards | **Plant their own traded cards** |

## Solution Implementation

See the refactored `main()` function with threading support.
