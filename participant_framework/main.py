"""
Main entry point: join a game on the live server using your chosen strategy.

To get started:
  1. Edit the CHOOSE YOUR STRATEGY section below.
  2. Edit config.py to set your player name, game ID, and server URL.
  3. Run:  python main.py
"""
from __future__ import annotations

import logging
import threading
import uuid

import config
from framework.api_client import GameApiClient
from framework.player_agent import PlayerAgent, start_agent_thread

# ══════════════════════════════════════════════════════
#  STEP 1: CHOOSE YOUR STRATEGY
#  Change the import and instantiation to use your own strategy class.
# ══════════════════════════════════════════════════════
from strategies.random_strategy import RandomStrategy
STRATEGY = RandomStrategy()
# ══════════════════════════════════════════════════════


def main():
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    # STEP 2: Edit config.py to set your player name, game ID, and server URL.
    player_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"bonanzha-{config.PLAYER_NAME}"))

    print(f"=== Bonanzha AI Agent ===")
    print(f"  Server:   {config.SERVER_URL}")
    print(f"  Game:     {config.GAME_ID}")
    print(f"  Player:   {config.PLAYER_NAME}")
    print(f"  Strategy: {type(STRATEGY).__name__}")
    print()

    api = GameApiClient(config.GAME_ID, config.SERVER_URL)
    print(f"  Joining game '{config.GAME_ID}' as '{config.PLAYER_NAME}' ...")
    try:
        api.join_game(config.PLAYER_NAME, player_id)
        print(f"  Registered! Player ID: {player_id}")
    except Exception as e:
        print(f"  Registration failed: {e}")
        print("  (If the game is already running, the agent will still try to play.)")

    agent = PlayerAgent(
        game_name=config.GAME_ID,
        player_id=player_id,
        player_name=config.PLAYER_NAME,
        strategy=STRATEGY,
        base_url=config.SERVER_URL,
    )

    stop_event = threading.Event()
    thread = start_agent_thread(agent, stop_event)
    print(f"  Agent running. Press Ctrl+C to stop.\n")

    try:
        while thread.is_alive():
            thread.join(timeout=2)
    except KeyboardInterrupt:
        print("\n  Stopping agent...")
        stop_event.set()
        thread.join(timeout=5)

    try:
        final_state = api.get_game(player_id)
        if final_state and hasattr(final_state, 'players') and final_state.players:
            print()
            print("━" * 54)
            print("  GAME OVER")
            print("━" * 54)
            ranked = sorted(final_state.players, key=lambda p: p.coins, reverse=True)
            for i, p in enumerate(ranked):
                marker = " <<< YOU" if p.name == config.PLAYER_NAME else ""
                print(f"  {i+1}. {p.name:<14} {p.coins:>4} coins{marker}")
            print("━" * 54)
    except Exception:
        pass


if __name__ == "__main__":
    main()
