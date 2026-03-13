"""
Board game client – application entry point.

Creates players, registers them with the server, and launches
autonomous PlayerAgent threads.
"""
import logging
import threading
import uuid
from time import sleep

from game_api_client import GameApiClient
from game_state_manager import GameStateManager
from player_agent import PlayerAgent, start_agent_thread


def main():
    """Main function to run the example client."""
    # ── Logging ──────────────────────────────────────────────────────
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()],
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting game client application")

    # ── Configuration ────────────────────────────────────────────────
    game_name = 'GAME1'
    base_url = 'http://localhost:5186'

    # A shared API client is used only for lobby actions (join / start).
    # Each PlayerAgent creates its own client for in‑game requests.
    lobby_api = GameApiClient(game_name, base_url)

    # Generate deterministic UUIDs (reproducible across runs)
    NAMESPACE = uuid.NAMESPACE_DNS
    players = [
        {'id': str(uuid.uuid5(NAMESPACE, 'game-alice')),   'name': 'Alice'},
        {'id': str(uuid.uuid5(NAMESPACE, 'game-bob')),     'name': 'Bob'},
        {'id': str(uuid.uuid5(NAMESPACE, 'game-charlie')), 'name': 'Charlie'},
        {'id': str(uuid.uuid5(NAMESPACE, 'game-dave')),    'name': 'Dave'},
    ]

    # ── Register players ─────────────────────────────────────────────
    logger.info(f"Registering {len(players)} players")
    for p in players:
        try:
            lobby_api.join_game(p['name'], p['id'])
        except Exception as e:
            logger.error(f"Error joining game for {p['name']}: {e}", exc_info=True)
    logger.info("All players registered.")

    # ── Countdown & start ────────────────────────────────────────────
    print(f"Starting game {game_name}. Starting in 5 seconds...")
    for i in range(5, 0, -1):
        print(f"Countdown: {i}")
        sleep(1)

    try:
        lobby_api.start_game()
    except Exception as e:
        logger.error(f"Error starting game: {e}", exc_info=True)

    # ── Launch agent threads ─────────────────────────────────────────
    stop_event = threading.Event()
    agents = [
        PlayerAgent(game_name, p['id'], p['name'], base_url) for p in players
    ]
    threads = [start_agent_thread(agent, stop_event) for agent in agents]
    logger.info(f"Started {len(threads)} player agent threads")

    # ── Wait for game to finish ───────────────────────────────────────
    state_mgr = GameStateManager(lobby_api)
    final_state = None
    try:
        while not state_mgr.is_game_over():
            sleep(5)
        final_state = lobby_api.get_game()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    finally:
        stop_event.set()
        for thread in threads:
            thread.join(timeout=5)

    # ── Game-over results ─────────────────────────────────────────────
    print()
    print("━" * 54)
    print("  GAME OVER")
    print("━" * 54)
    if final_state and hasattr(final_state, 'players') and final_state.players:
        ranked = sorted(final_state.players, key=lambda p: p.coins, reverse=True)
        print(f"  {'Rank':<6} {'Player':<14} {'Coins':>6}")
        print(f"  {'────':<6} {'──────────────':<14} {'─────':>6}")
        medals = ['🥇', '🥈', '🥉']
        for i, p in enumerate(ranked):
            medal = medals[i] if i < 3 else f"  {i+1}."
            print(f"  {medal:<6} {p.name:<14} {p.coins:>6}")
        print("━" * 54)
        print(f"  Winner: {ranked[0].name} with {ranked[0].coins} coin(s)!")
    else:
        print("  (Could not retrieve final scores)")
    print("━" * 54)
    print()


if __name__ == "__main__":
    main()