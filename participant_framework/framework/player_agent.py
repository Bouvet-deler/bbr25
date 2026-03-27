"""
Player agent orchestration.

Each PlayerAgent runs in its own thread, polling the game state and
delegating decisions to whatever Strategy class you plug in.
"""
import logging
import threading
from time import sleep

from .game_objects import GameStateDto
from .api_client import GameApiClient


class PlayerAgent:
    """Autonomous agent that plays the game on behalf of a single player.

    Works with ANY strategy class that implements the BaseStrategy interface.
    """

    def __init__(
        self,
        game_name: str,
        player_id: str,
        player_name: str,
        strategy,
        base_url: str = 'http://localhost:5186',
    ) -> None:
        self.player_id = player_id
        self.player_name = player_name
        self.logger = logging.getLogger(f"Agent.{player_name}")

        self.api = GameApiClient(game_name, base_url)
        self.strategy = strategy
        # Inject the API client into the strategy so it can make server calls
        self.strategy.api = self.api

    # ── Main loop ────────────────────────────────────────────────────

    def run(self, stop_event: threading.Event) -> None:
        """Main agent loop — runs until the game ends or stop is signalled."""
        self.logger.info(f"Player agent started for {self.player_name}")

        while not stop_event.is_set():
            try:
                game_state = self.api.get_game(player_id=self.player_id)
                if not isinstance(game_state, GameStateDto):
                    sleep(2)
                    continue

                if game_state.current_state == 'GameDone':
                    self.logger.info("Game is over")
                    break

                if game_state.current_state != 'Playing':
                    sleep(2)
                    continue

                current_player = self._find_current_player(game_state)
                if not current_player:
                    sleep(2)
                    continue

                is_my_turn = (current_player.name == self.player_name)

                if is_my_turn:
                    self._handle_my_turn(game_state, current_player)
                    sleep(1)
                else:
                    self._handle_other_turn(game_state, current_player)
                    sleep(2)

            except Exception as e:
                self.logger.error(f"Error in {self.player_name} agent: {e}", exc_info=True)
                sleep(2)

        self.logger.info(f"Player agent stopped for {self.player_name}")

    # ── Turn handling ────────────────────────────────────────────────

    def _handle_my_turn(self, game_state: GameStateDto, current_player) -> None:
        fresh_state = self.api.get_game(player_id=self.player_id)
        fresh_player = next(
            (p for p in fresh_state.players if p.name == self.player_name), current_player
        )
        phase = fresh_state.current_phase

        print(f"\n{'━' * 54}")
        print(f"  {phase} │ {fresh_player.name} │ deck: {fresh_state.deck} │ {fresh_player.coins} coins")
        print(f"{'━' * 54}")

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

        except Exception as e:
            print(f"  ✗ Error during {phase}: {e}")

    def _handle_other_turn(self, game_state: GameStateDto, current_player) -> None:
        if game_state.current_phase == 'Trading':
            sleep(3)
            fresh_state = self.api.get_game(player_id=self.player_id)
            my_data = next((p for p in fresh_state.players if p.name == self.player_name), None)
            if my_data:
                self.strategy.optional_trading_strategy(fresh_state, my_data, self.player_id)

        elif game_state.current_phase == 'TradePlanting':
            my_data = next((p for p in game_state.players if p.name == self.player_name), None)
            if my_data and my_data.traded_cards:
                print(f"\n{'━' * 54}")
                print(f"  TradePlanting │ {self.player_name} (non-active) │ planting traded cards")
                print(f"{'━' * 54}")
                self.strategy.trade_planting_strategy(game_state, my_data, self.player_id)

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _find_current_player(game_state: GameStateDto):
        for player in game_state.players:
            if player.name == game_state.current_player:
                return player
        return None


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
