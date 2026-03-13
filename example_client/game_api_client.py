"""
Pure REST API client for the board game server.

This module handles all HTTP communication with the game server.
No game logic or strategy decisions belong here.
"""
import logging
import uuid

import requests

from game_objects import GameStateDto, dict_to_game_state, OfferDto, Accept


class GameApiClient:
    """Handles all REST API communication with the board game server."""

    def __init__(self, game_name: str, base_url: str = 'http://localhost:5186') -> None:
        self.logger = logging.getLogger(f"ApiClient.{game_name}")
        self.game_name = game_name
        self.base_url = base_url

    # ── Game Management ──────────────────────────────────────────────

    def get_all_games(self, player_id: str | None = None) -> list[GameStateDto]:
        """Get all available games."""
        url = f"{self.base_url}/api/game/all"
        params = {}
        if player_id:
            params['playerId'] = player_id
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Failed to get all games: {response.status_code} - {response.text}")
        return [dict_to_game_state(game) for game in response.json()]

    def get_game(self, player_id: str | None = None) -> GameStateDto:
        """Get current game state."""
        url = f"{self.base_url}/api/game"
        params = {'gameName': self.game_name}
        if player_id:
            params['playerId'] = player_id
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Failed to get game state: {response.status_code} - {response.text}")
        return dict_to_game_state(response.json())

    def join_game(self, player_name: str, player_id: str | None = None) -> str:
        """Join a game. Returns response text."""
        url = f"{self.base_url}/api/game/join"
        params = {
            'gameName': self.game_name,
            'playerKey': player_id if player_id else str(uuid.uuid4()),
            'name': player_name
        }
        self.logger.debug(f"Joining game with player: {player_name}")
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Failed to join game: {response.status_code} - {response.text}")
        self.logger.info(f"Successfully joined as {player_name}")
        return response.text

    def start_game(self) -> str:
        """Start the game. Returns response text."""
        url = f"{self.base_url}/api/game/start"
        params = {'gameName': self.game_name}
        self.logger.info(f"Attempting to start game: {self.game_name}")
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Failed to start game: {response.status_code} - {response.text}")
        self.logger.info("Game started successfully")
        return response.text

    def check_for_timeout(self) -> bool:
        """Check if the game phase has timed out."""
        url = f"{self.base_url}/api/game/check-for-timeout"
        params = {'gameName': self.game_name}
        response = requests.get(url, params=params, timeout=5)
        return response.status_code == 200

    def stop_game(self) -> bool:
        """Stop the game."""
        url = f"{self.base_url}/api/game/stop"
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Failed to stop game: {response.status_code} - {response.text}")
        return True

    # ── Scoring ──────────────────────────────────────────────────────

    def get_scores(self) -> dict:
        """Get current scores. Returns dict of player_name -> coins."""
        url = f"{self.base_url}/api/score/get"
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Failed to get scores: {response.status_code} - {response.text}")
        return response.json()

    # ── Playing Actions ──────────────────────────────────────────────

    def plant(self, player_id: str, field_id: str):
        """Plant the top card from hand onto a field."""
        url = f"{self.base_url}/api/playing/plant"
        params = {'gameName': self.game_name, 'playerId': player_id, 'fieldId': field_id}
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Failed to plant: {response.status_code} - {response.text}")
        return response.json()

    def end_planting(self, player_id: str) -> str:
        """End the planting phase."""
        url = f"{self.base_url}/api/playing/end-planting"
        params = {'gameName': self.game_name, 'playerId': player_id}
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Failed to end planting: {response.status_code} - {response.text}")
        return response.text

    def end_trading(self, player_id: str) -> str:
        """End the trading phase."""
        url = f"{self.base_url}/api/playing/end-trading"
        params = {'gameName': self.game_name, 'playerId': player_id}
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Failed to end trading: {response.status_code} - {response.text}")
        return response.text

    def trade_plant(self, player_id: str, card_id: str, field_id: str):
        """Plant a traded/drawn card onto a field."""
        url = f"{self.base_url}/api/playing/trade-plant"
        params = {
            'gameName': self.game_name,
            'playerId': player_id,
            'cardId': card_id,
            'fieldId': field_id,
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Failed to trade plant: {response.status_code} - {response.text}")
        return response.json()

    def harvest_field(self, player_id: str, field_id: str) -> str:
        """Harvest a field."""
        url = f"{self.base_url}/api/playing/harvest-field"
        params = {
            'gameName': self.game_name,
            'playerId': player_id,
            'fieldId': field_id,
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Failed to harvest field: {response.status_code} - {response.text}")
        return response.text

    def request_trade(self, player_id: str, offered_cards: list[str], card_types_wanted: list[str]) -> str:
        """Post a trade offer."""
        url = f"{self.base_url}/api/playing/request-trade"
        params = {'gameName': self.game_name, 'playerId': player_id}
        payload = {
            'offeredCards': offered_cards,
            'cardTypesWanted': card_types_wanted,
        }
        response = requests.post(url, params=params, json=payload, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Failed to request trade: {response.status_code} - {response.text}")
        return response.text

    def accept_trade(self, player_id: str, negotiation_id: str, payment: list[str]) -> str:
        """Accept a trade offer."""
        url = f"{self.base_url}/api/playing/accept-trade"
        params = {'gameName': self.game_name, 'playerId': player_id}
        payload = {
            'negotiationId': negotiation_id,
            'payment': payment,
        }
        response = requests.post(url, params=params, json=payload, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Failed to accept trade: {response.status_code} - {response.text}")
        return response.text
