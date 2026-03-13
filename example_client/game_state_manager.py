"""
Game state tracking and helper queries.

Maintains game history and provides utility methods for
querying the current game state without making decisions.
"""
import logging

from game_objects import GameStateDto, PlayerDto
from game_api_client import GameApiClient


class GameStateManager:
    """Tracks game state history and provides state query helpers."""

    def __init__(self, api: GameApiClient) -> None:
        self.logger = logging.getLogger(f"StateManager.{api.game_name}")
        self.api = api
        self.previous_game_state: GameStateDto | None = None
        self.all_seen_game_states: list[GameStateDto] = []
        self.all_seen_cards: list = []

    def update(self, game_state: GameStateDto) -> None:
        """Record a game state snapshot."""
        self.previous_game_state = game_state
        self.all_seen_game_states.append(game_state)

    def is_game_over(self) -> bool:
        """Check whether the game has ended."""
        game_state = self.api.get_game()
        if isinstance(game_state, GameStateDto):
            return game_state.current_state == 'GameDone'
        return False

    @staticmethod
    def get_current_player(game_state: GameStateDto) -> PlayerDto | None:
        """Return the PlayerDto whose turn it is, or None."""
        if not isinstance(game_state, GameStateDto):
            raise Exception("Invalid game state object")
        for player in game_state.players:
            if player.name == game_state.current_player:
                return player
        return None

    def get_player_hand(self, player_id: str) -> list:
        """Fetch the actual cards in a player's hand from the server."""
        game_state = self.api.get_game(player_id=player_id)
        if isinstance(game_state, GameStateDto):
            return game_state.your_hand
        return []

    def get_fresh_state(self, player_id: str | None = None) -> GameStateDto:
        """Fetch a fresh game state from the server."""
        return self.api.get_game(player_id=player_id)
