"""
Entry point for running the RL agent against the live Bonanzha server.

Can run RL agents alongside or against rule-based agents from example_client.

Usage:
    # Run 2 RL + 2 rule-based agents
    python main.py --game GAME1 --rl-players 2 --rule-players 2

    # Run 4 RL agents
    python main.py --game GAME1 --rl-players 4

    # Use specific model
    python main.py --game GAME1 --model models/best.pt --rl-players 4
"""
from __future__ import annotations

import argparse
import logging
import sys
import threading
import uuid
from pathlib import Path
from time import sleep

# Add example_client to path for shared modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "example_client"))

from game_api_client import GameApiClient
from game_state_manager import GameStateManager
from game_objects import GameStateDto
from player_agent import PlayerAgent, start_agent_thread
from rl_strategy import RLStrategy


class RLPlayerAgent(PlayerAgent):
    """PlayerAgent that uses RLStrategy instead of rule-based GameStrategy."""

    def __init__(
        self,
        game_name: str,
        player_id: str,
        player_name: str,
        model_path: str = "models/best.pt",
        base_url: str = "http://localhost:5186",
    ):
        super().__init__(game_name, player_id, player_name, base_url)
        # Replace the strategy with the RL-based one
        self.strategy = RLStrategy(self.api, model_path=model_path)


def main():
    parser = argparse.ArgumentParser(description="Run Bonanzha RL agent against live server")
    parser.add_argument("--game", type=str, default="GAME1")
    parser.add_argument("--base-url", type=str, default="http://localhost:5186")
    parser.add_argument("--model", type=str, default="models/best.pt")
    parser.add_argument("--rl-players", type=int, default=4, help="Number of RL agents")
    parser.add_argument("--rule-players", type=int, default=0, help="Number of rule-based agents")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    logger = logging.getLogger(__name__)

    game_name = args.game
    base_url = args.base_url
    total = args.rl_players + args.rule_players
    if total < 2 or total > 5:
        print(f"Total players must be 2-5, got {total}")
        return

    NAMESPACE = uuid.NAMESPACE_DNS
    rl_names = [f"RL-Agent-{i+1}" for i in range(args.rl_players)]
    rule_names = [f"Rule-{chr(65+i)}" for i in range(args.rule_players)]
    all_names = rl_names + rule_names

    players = [
        {"id": str(uuid.uuid5(NAMESPACE, f"game-{name.lower()}")), "name": name}
        for name in all_names
    ]

    lobby_api = GameApiClient(game_name, base_url)

    # Register
    for p in players:
        try:
            lobby_api.join_game(p["name"], p["id"])
        except Exception as e:
            logger.error(f"Error joining for {p['name']}: {e}")

    # Countdown
    print(f"\nStarting game {game_name} with {len(players)} players:")
    for p in players:
        kind = "RL" if p["name"].startswith("RL") else "Rule-based"
        print(f"  {p['name']} ({kind})")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        sleep(1)

    try:
        lobby_api.start_game()
    except Exception as e:
        logger.error(f"Error starting game: {e}")
        return

    # Build agents
    stop_event = threading.Event()
    agents = []
    for i, p in enumerate(players):
        if i < args.rl_players:
            agent = RLPlayerAgent(game_name, p["id"], p["name"], args.model, base_url)
        else:
            agent = PlayerAgent(game_name, p["id"], p["name"], base_url)
        agents.append(agent)

    threads = [start_agent_thread(agent, stop_event) for agent in agents]

    # Wait for game to finish
    state_mgr = GameStateManager(lobby_api)
    final_state = None
    try:
        while not state_mgr.is_game_over():
            sleep(5)
        final_state = lobby_api.get_game()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        stop_event.set()
        for t in threads:
            t.join(timeout=5)

    # Results
    print()
    print("━" * 54)
    print("  GAME OVER")
    print("━" * 54)
    if final_state and hasattr(final_state, "players") and final_state.players:
        ranked = sorted(final_state.players, key=lambda p: p.coins, reverse=True)
        rl_set = set(rl_names)
        print(f"  {'Rank':<6} {'Player':<18} {'Type':<10} {'Coins':>6}")
        print(f"  {'────':<6} {'──────────────────':<18} {'────────':<10} {'─────':>6}")
        medals = ["🥇", "🥈", "🥉"]
        for i, p in enumerate(ranked):
            medal = medals[i] if i < 3 else f"  {i+1}."
            kind = "RL" if p.name in rl_set else "Rule"
            print(f"  {medal:<6} {p.name:<18} {kind:<10} {p.coins:>6}")
        print("━" * 54)
        winner = ranked[0]
        kind = "RL" if winner.name in rl_set else "Rule"
        print(f"  Winner: {winner.name} ({kind}) with {winner.coins} coin(s)!")
    else:
        print("  (Could not retrieve final scores)")
    print("━" * 54)


if __name__ == "__main__":
    main()
