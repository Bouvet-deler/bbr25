"""
Player agent orchestration.

Each PlayerAgent runs in its own thread, polling the game state and
delegating decisions to GameStrategy.  It owns instances of the API
client, state manager, and strategy.
"""
import logging
import threading
from time import sleep

from game_objects import GameStateDto
from game_api_client import GameApiClient
from game_state_manager import GameStateManager
from game_strategy import GameStrategy


class PlayerAgent:
    """Autonomous agent that plays the game on behalf of a single player."""

    def __init__(self, game_name: str, player_id: str, player_name: str, base_url: str = 'http://localhost:5186') -> None:
        self.player_id = player_id
        self.player_name = player_name
        self.logger = logging.getLogger(f"Agent.{player_name}")

        # Each agent gets its own set of collaborators
        self.api = GameApiClient(game_name, base_url)
        self.state_manager = GameStateManager(self.api)
        self.strategy = GameStrategy(self.api)

    # ── Main loop ────────────────────────────────────────────────────

    def run(self, stop_event: threading.Event) -> None:
        """Main agent loop — runs until the game ends or stop is signalled."""
        self.logger.info(f"Player agent started for {self.player_name}")

        while not stop_event.is_set() and not self.state_manager.is_game_over():
            try:
                game_state = self.api.get_game(player_id=self.player_id)
                if not isinstance(game_state, GameStateDto):
                    sleep(2)
                    continue

                current_player = GameStateManager.get_current_player(game_state)
                if not current_player:
                    sleep(2)
                    continue

                is_my_turn = (current_player.name == self.player_name)

                if is_my_turn:
                    self._handle_my_turn(game_state, current_player)
                    sleep(4)
                else:
                    self._handle_other_turn(game_state, current_player)
                    sleep(2)

            except Exception as e:
                self.logger.error(f"Error in {self.player_name} agent: {e}", exc_info=True)
                sleep(2)

        self.logger.info(f"Player agent stopped for {self.player_name}")

    # ── Turn handling ────────────────────────────────────────────────

    def _handle_my_turn(self, game_state: GameStateDto, current_player) -> None:
        """Dispatch to the appropriate strategy for the current phase."""
        # Always fetch fresh state so strategies see the real server state
        fresh_state = self.api.get_game(player_id=self.player_id)
        fresh_player = next(
            (p for p in fresh_state.players if p.name == self.player_name), current_player
        )
        phase = fresh_state.current_phase
        deck  = fresh_state.deck

        print(f"\n{'\u2501'*54}")
        print(f"  {phase} \u2502 {fresh_player.name} \u2502 deck: {deck} \u2502 {fresh_player.coins} coins")
        print(f"{'\u2501'*54}")

        try:
            if phase == 'Planting':
                self.strategy.planting_strategy(fresh_state, fresh_player, self.player_id)

            elif phase == 'PlantingOptional':
                self.strategy.optional_planting_strategy(fresh_state, fresh_player, self.player_id)

            elif phase == 'Trading':
                self.strategy.trading_strategy(fresh_state, fresh_player, self.player_id)

            elif phase == 'TradePlanting':
                self.strategy.trade_planting_strategy(fresh_state, fresh_player, self.player_id)
                self.strategy.last_round_harvest_strategy(fresh_state, fresh_player, self.player_id)
                self._print_turn_summary(fresh_state)

        except Exception as e:
            print(f"  ✗ Error during {phase}: {e}")
        finally:
            self.state_manager.update(fresh_state)

    def _handle_other_turn(self, game_state: GameStateDto, current_player) -> None:
        """Handle phases where non-current players may participate."""
        if game_state.current_phase == 'Trading':
            sleep(3)  # Give current player time to post trade first
            # Re-fetch state so we see the posted trades
            fresh_state = self.api.get_game(player_id=self.player_id)
            my_data = next((p for p in fresh_state.players if p.name == self.player_name), None)
            if my_data:
                self.strategy.optional_trading_strategy(fresh_state, my_data, self.player_id)

        elif game_state.current_phase == 'TradePlanting':
            my_data = next((p for p in game_state.players if p.name == self.player_name), None)
            if my_data and my_data.traded_cards:
                print(f"\n{'\u2501'*54}")
                print(f"  TradePlanting \u2502 {self.player_name} (non-active) \u2502 planting traded cards")
                print(f"{'\u2501'*54}")
                self.strategy.trade_planting_strategy(game_state, my_data, self.player_id)

    # ── Display helpers ──────────────────────────────────────────────

    def _print_turn_summary(self, game_state: GameStateDto) -> None:
        """Print a coin scoreboard for all players after a full turn completes."""
        try:
            fresh_state = self.api.get_game()
            print(f"\n  \ud83d� Scoreboard after {game_state.current_player}'s turn:")
            for player in fresh_state.players:
                fields_str = GameStrategy._fmt_fields(player.fields)
                print(f"     {player.name}: {player.coins} coins  —  {fields_str}")
        except Exception as e:
            self.logger.debug(f"Could not fetch turn summary: {e}")


def start_agent_thread(agent: PlayerAgent, stop_event: threading.Event) -> threading.Thread:
    """Create and start a daemon thread running the given agent."""
    thread = threading.Thread(
        target=agent.run,
        args=(stop_event,),
        name=f"Agent-{agent.player_name}",
        daemon=True,
    )
    thread.start()
    return thread
