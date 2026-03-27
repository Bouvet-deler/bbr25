"""
Base strategy classes for Bonanzha player agents.

Two abstract base classes are provided:

1. BaseStrategy — Override individual phase methods (planting_strategy,
   trading_strategy, etc.) for full control over game logic.
   Best for: rule-based, statistical, Bayesian approaches.

2. ActionStrategy — Override a single select_action() method that maps
   (observation_vector, legal_actions, phase) → action_index.
   The framework handles encoding, legal action computation, and API calls.
   Best for: RL, Q-learning, evolutionary, MCTS approaches.

ActionStrategy's action encoding matches the simulator exactly, so models
trained offline work live against the server with zero translation.
"""
from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from collections import Counter
from time import sleep
from typing import List

import numpy as np

from framework.api_client import GameApiClient
from framework.game_objects import FieldDto, GameStateDto, HandCardDto, PlayerDto, CardDto
from framework.card_config import NAME_TO_INDEX, harvest_value as hv_lookup
from framework.state_encoder import STATE_SIZE, encode_live_state, PHASE_NAME_TO_IDX


# ─────────────────────────────────────────────────────────────────────
#  BaseStrategy — override phase methods for full control
# ─────────────────────────────────────────────────────────────────────

class BaseStrategy(ABC):
    """Abstract base for strategies that implement per-phase game logic.

    Subclass this if you want full control over each phase (what to plant,
    when to harvest, how to trade). Provides common utility methods used
    by all strategies.
    """

    def __init__(self) -> None:
        self.api: GameApiClient = None  # injected by PlayerAgent
        self.logger = logging.getLogger(self.__class__.__name__)

    # ── Abstract phase methods (YOU implement these) ─────────────────

    @abstractmethod
    def planting_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        """Called when it's your turn and the phase is Planting.

        You MUST plant the first card from your hand onto one of your 2 fields.
        If no field matches, you must harvest a field first to make room.

        Available API calls:
          - self.api.plant(player_id, field_id)
          - self.api.harvest_field(player_id, field_id)
          - self.api.get_game(player_id=player_id)  (to refresh state)
        """
        ...

    @abstractmethod
    def optional_planting_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        """Called when it's your turn and the phase is PlantingOptional.

        You MAY plant one more card or skip. Call self.api.end_planting()
        to skip, or self.api.plant() to plant.
        """
        ...

    @abstractmethod
    def trading_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        """Called when it's your turn and the phase is Trading.

        You drew 2 cards (visible in current_player.drawn_cards).
        You may post trade offers, then MUST call self.api.end_trading().

        Available API calls:
          - self.api.request_trade(player_id, offered_card_ids, wanted_types)
          - self.api.end_trading(player_id)
        """
        ...

    @abstractmethod
    def trade_planting_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        """Called during TradePlanting: plant all traded + drawn cards.

        All cards in current_player.traded_cards (and drawn_cards if you're
        the active player) must be planted using self.api.trade_plant().
        """
        ...

    @abstractmethod
    def optional_trading_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        """Called when ANOTHER player is trading and you can accept their offers.

        Check game_state.available_trades for posted offers. Accept with:
          self.api.accept_trade(player_id, negotiation_id, payment_card_ids)
        """
        ...

    # ── Default: last round harvest (can be overridden) ──────────────

    def last_round_harvest_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        """Harvest everything when the deck is nearly empty.

        Called at the end of TradePlanting. Override if you want custom
        end-of-game logic. Default: harvest all harvestable fields on the
        last deck pass when fewer than (num_players * 5) cards remain.
        """
        num_players = len(game_state.players)
        last_round_threshold = num_players * 5
        if game_state.round < 2 or game_state.deck > last_round_threshold:
            return

        print(f"  ⚠ Last deck pass, {game_state.deck} cards left — harvesting")
        fresh_state = self.api.get_game(player_id=player_id)
        fresh_player = next(
            (p for p in fresh_state.players if p.name == current_player.name),
            current_player,
        )

        for field in list(fresh_player.fields):
            if field.card and self.can_harvest_field(fresh_player, field):
                try:
                    self.api.harvest_field(player_id, field.key)
                    coins = self.harvest_value(field)
                    print(f"   → Harvested {len(field.card)}×{field.card[0].type} → {coins} coins")
                except Exception:
                    break
                fresh_state = self.api.get_game(player_id=player_id)
                fresh_player = next(
                    (p for p in fresh_state.players if p.name == current_player.name),
                    fresh_player,
                )

    # ── Utility methods (available to all strategies) ────────────────

    @staticmethod
    def can_harvest_field(player: PlayerDto, field: FieldDto) -> bool:
        """Check if a field can be harvested (bean-protection rule).

        Rule: Cannot harvest a field with only 1 card if ANY other field has 2+ cards.
        Fields with 2+ cards can always be harvested. Empty fields cannot.
        """
        field_size = len(field.card)
        if field_size >= 2:
            return True
        if field_size == 0:
            return False
        for other_field in player.fields:
            if other_field.key != field.key and len(other_field.card) >= 2:
                return False
        return True

    @staticmethod
    def harvest_value(field: FieldDto) -> int:
        """Calculate the coin payout for harvesting this field right now."""
        num_cards = len(field.card)
        if num_cards == 0:
            return 0
        for entry in field.card[0].exchange_map:
            if num_cards >= entry.crop_size:
                return entry.value
        return 0

    @staticmethod
    def fmt_hand(cards) -> str:
        """Format a card list as 'TypeA×3, TypeB, …' grouped by type."""
        if not cards:
            return "(empty)"
        counts = Counter(c.type for c in cards)
        return ", ".join(f"{t}×{n}" if n > 1 else t for t, n in counts.items())

    @staticmethod
    def fmt_fields(fields: list[FieldDto]) -> str:
        """Format fields as 'Field 1: TypeA×3  |  Field 2: empty'."""
        parts = []
        for i, f in enumerate(fields, 1):
            if f.card:
                parts.append(f"Field {i}: {f.card[0].type}×{len(f.card)}")
            else:
                parts.append(f"Field {i}: empty")
        return "  |  ".join(parts)


# ─────────────────────────────────────────────────────────────────────
#  ActionStrategy — override select_action() for ML approaches
# ─────────────────────────────────────────────────────────────────────

class ActionStrategy(BaseStrategy):
    """Abstract base for strategies that pick actions from encoded state.

    You only need to implement ONE method:
        select_action(observation, legal_actions, phase) → action_index

    The framework handles:
      - Encoding game state into a 75-element float vector
      - Computing which actions are legal
      - Translating the chosen action into API calls

    Action encoding per phase (matches the simulator exactly):

    Planting / PlantingOptional:
      0 = plant on field 0
      1 = plant on field 1
      2 = skip / end planting  (only valid in PlantingOptional)
      3 = harvest field 0 then plant
      4 = harvest field 1 then plant

    Trading:
      0 = skip trading
      1 = offer undesired drawn cards
      2 = offer ALL drawn cards
      3 = offer 1 undesired hand card
      4 = offer undesired drawn + 1 undesired hand card
      5 = offer all drawn + 1 undesired hand card

    TradePlanting:
      0 = place on field 0
      1 = place on field 1
      2 = harvest field 0 then place
      3 = harvest field 1 then place
    """

    @abstractmethod
    def select_action(
        self, observation: np.ndarray, legal_actions: List[int], phase: int
    ) -> int:
        """Choose an action given the current state.

        Parameters
        ----------
        observation : np.ndarray
            75-element float vector encoding the game state.
            See framework/state_encoder.py for the full layout.
        legal_actions : List[int]
            Action indices that are currently legal. Your return value
            MUST be one of these.
        phase : int
            Current phase: 0=Planting, 1=PlantingOptional, 2=Trading, 3=TradePlanting.

        Returns
        -------
        int
            The chosen action index (must be in legal_actions).
        """
        ...

    def encode_state(
        self, game_state: GameStateDto, player: PlayerDto, phase_idx: int
    ) -> np.ndarray:
        """Encode game state into observation vector.

        Override this to use a custom state representation.
        Default: the standard 75-element encoding from state_encoder.py.
        """
        return encode_live_state(game_state, player, phase_idx)

    # ── Phase implementations (auto-dispatch to select_action) ───────

    def planting_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        cards_in_hand = self.api.get_game(player_id=player_id).your_hand
        if not cards_in_hand:
            self.api.end_planting(player_id)
            return

        print(f"  Hand ({len(cards_in_hand)}): {self.fmt_hand(cards_in_hand)}")
        print(f"  Fields: {self.fmt_fields(current_player.fields)}")

        obs = self.encode_state(game_state, current_player, 0)
        legal = self._legal_planting(current_player, cards_in_hand)
        action = self.select_action(obs, legal, 0)

        card_type = cards_in_hand[0].type

        if action in (0, 1):
            field = current_player.fields[action]
            if field.card and field.card[0].type != card_type:
                if self.can_harvest_field(current_player, field):
                    self.api.harvest_field(player_id, field.key)
                    print(f"  → Harvested Field {action + 1}")
                else:
                    action = self._legal_planting(current_player, cards_in_hand)[0]
                    field = current_player.fields[action] if action in (0, 1) else current_player.fields[0]
            self.api.plant(player_id, current_player.fields[action if action in (0, 1) else 0].key)
            print(f"  → Planted {card_type} on Field {action + 1}")

        elif action in (3, 4):
            fi = action - 3
            if self.can_harvest_field(current_player, current_player.fields[fi]):
                self.api.harvest_field(player_id, current_player.fields[fi].key)
                print(f"  → Harvested Field {fi + 1}")
            self.api.plant(player_id, current_player.fields[fi].key)
            print(f"  → Planted {card_type} on Field {fi + 1}")

        fresh = self.api.get_game(player_id=player_id)
        fresh_p = next((p for p in fresh.players if p.name == current_player.name), current_player)
        current_player.fields = fresh_p.fields
        print(f"  Fields after: {self.fmt_fields(current_player.fields)}")

    def optional_planting_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        fresh_state = self.api.get_game(player_id=player_id)
        cards_in_hand = fresh_state.your_hand
        if not cards_in_hand:
            self.api.end_planting(player_id)
            return

        fresh_player = next(
            (p for p in fresh_state.players if p.name == current_player.name), current_player
        )
        obs = self.encode_state(fresh_state, fresh_player, 1)
        legal = self._legal_optional(fresh_player, cards_in_hand)
        action = self.select_action(obs, legal, 1)

        card_type = cards_in_hand[0].type

        if action == 2:
            print(f"  → Skipping optional plant")
            self.api.end_planting(player_id)
            return

        if action in (0, 1):
            f = fresh_player.fields[action]
            if f.card and f.card[0].type != card_type:
                self.api.end_planting(player_id)
                return
            self.api.plant(player_id, f.key)
            print(f"  → Optional-planted {card_type} on Field {action + 1}")

        elif action in (3, 4):
            fi = action - 3
            if self.can_harvest_field(fresh_player, fresh_player.fields[fi]):
                self.api.harvest_field(player_id, fresh_player.fields[fi].key)
            self.api.plant(player_id, fresh_player.fields[fi].key)
            print(f"  → Optional-planted {card_type} on Field {fi + 1}")

        updated = self.api.get_game(player_id=player_id)
        refreshed = next((p for p in updated.players if p.name == current_player.name), None)
        if refreshed:
            current_player.fields = refreshed.fields
        print(f"  Fields after: {self.fmt_fields(current_player.fields)}")

    def trading_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        turned_over = list(current_player.drawn_cards)[:2]
        cards_in_hand = self.api.get_game(player_id=player_id).your_hand

        print(f"  Fields: {self.fmt_fields(current_player.fields)}")
        print(f"  Drawn:  {self.fmt_hand(turned_over)}")
        print(f"  Hand ({len(cards_in_hand)}): {self.fmt_hand(cards_in_hand)}")

        obs = self.encode_state(game_state, current_player, 2)
        legal = self._legal_trading(current_player, cards_in_hand)
        action = self.select_action(obs, legal, 2)

        owned_types = {f.card[0].type for f in current_player.fields if f.card}

        if action == 0:
            print(f"  → Skipping trade")
            self.api.end_trading(player_id)
            return

        undesired_drawn = [c for c in turned_over if c.type not in owned_types]
        undesired_hand = [c for c in cards_in_hand if c.type not in owned_types]

        cards_to_offer = []
        if action == 1:
            cards_to_offer = undesired_drawn
        elif action == 2:
            cards_to_offer = turned_over
        elif action == 3:
            cards_to_offer = undesired_hand[:1]
        elif action == 4:
            cards_to_offer = undesired_drawn + undesired_hand[:1]
        elif action == 5:
            cards_to_offer = turned_over + undesired_hand[:1]

        desired_types = list(owned_types) if owned_types else []

        if not cards_to_offer or not desired_types:
            self.api.end_trading(player_id)
            return

        try:
            self.api.request_trade(player_id, [c.id for c in cards_to_offer], desired_types)
            offer_str = ', '.join(c.type for c in cards_to_offer)
            print(f"  → Offering [{offer_str}] for any {desired_types}")
            sleep(5)
        except Exception as e:
            self.logger.error(f"Trade offer error: {e}")

        self.api.end_trading(player_id)

    def trade_planting_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        remaining = list(current_player.traded_cards)
        if current_player.name == game_state.current_player:
            remaining += current_player.drawn_cards[:2]

        if not remaining:
            print(f"  (no cards to trade-plant)")
            return

        print(f"  Must plant: {self.fmt_hand(remaining)}")

        for card in remaining:
            fresh = self.api.get_game(player_id=player_id)
            fresh_p = next(
                (p for p in fresh.players if p.name == current_player.name), current_player
            )

            obs = self.encode_state(fresh, fresh_p, 3)
            legal = self._legal_trade_plant(fresh_p, card.type)
            action = self.select_action(obs, legal, 3)

            if action in (0, 1):
                f = fresh_p.fields[action]
                if f.card and f.card[0].type != card.type:
                    if self.can_harvest_field(fresh_p, f):
                        self.api.harvest_field(player_id, f.key)
                self.api.trade_plant(player_id, card.id, f.key)
                print(f"  → Trade-planted {card.type} on Field {action + 1}")

            elif action in (2, 3):
                fi = action - 2
                if self.can_harvest_field(fresh_p, fresh_p.fields[fi]):
                    self.api.harvest_field(player_id, fresh_p.fields[fi].key)
                self.api.trade_plant(player_id, card.id, fresh_p.fields[fi].key)
                print(f"  → Trade-planted {card.type} on Field {fi + 1}")

        final = self.api.get_game(player_id=player_id)
        final_p = next((p for p in final.players if p.name == current_player.name), None)
        if final_p:
            print(f"  Fields after: {self.fmt_fields(final_p.fields)}")

    def optional_trading_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        """Default trade acceptance: accept if offered cards match our fields."""
        posted_trades = game_state.available_trades
        if not posted_trades:
            return

        owned_types = {f.card[0].type for f in current_player.fields if f.card}

        for trade in posted_trades:
            wanted = [t for t in trade.offered_cards if t in owned_types]
            if not wanted:
                continue

            matching_hand = [c for c in game_state.your_hand if c.type in trade.card_types_wanted]
            if not matching_hand:
                continue

            type_counts = Counter(c.type for c in matching_hand)
            best_type = max(type_counts, key=type_counts.get)
            card_to_give = next(c for c in matching_hand if c.type == best_type)

            try:
                self.api.accept_trade(player_id, trade.negotiation_id, [card_to_give.id])
                print(f"  🤝 Accepted trade: gave {card_to_give.type}, receiving {wanted}")
                return
            except Exception as e:
                if "404" not in str(e):
                    self.logger.error(f"Error accepting trade: {e}")

    # ── Legal action computation ─────────────────────────────────────

    @staticmethod
    def _legal_planting(player: PlayerDto, hand: list) -> List[int]:
        if not hand:
            return [0]
        card_type = hand[0].type
        actions = []
        for fi, f in enumerate(player.fields[:2]):
            if not f.card or f.card[0].type == card_type:
                actions.append(fi)
        if not actions:
            for fi, f in enumerate(player.fields[:2]):
                if BaseStrategy.can_harvest_field(player, f):
                    actions.append(3 + fi)
        return actions if actions else [0]

    @staticmethod
    def _legal_optional(player: PlayerDto, hand: list) -> List[int]:
        actions = [2]  # skip always legal
        if not hand:
            return actions
        card_type = hand[0].type
        for fi, f in enumerate(player.fields[:2]):
            if not f.card or f.card[0].type == card_type:
                actions.append(fi)
        for fi, f in enumerate(player.fields[:2]):
            if f.card and f.card[0].type != card_type and BaseStrategy.can_harvest_field(player, f):
                actions.append(3 + fi)
        return actions

    @staticmethod
    def _legal_trading(player: PlayerDto, hand_cards: list) -> List[int]:
        actions = [0]
        owned_types = {f.card[0].type for f in player.fields if f.card}
        has_undesired_drawn = any(c.type not in owned_types for c in player.drawn_cards)
        has_undesired_hand = any(c.type not in owned_types for c in hand_cards)

        if has_undesired_drawn:
            actions.append(1)
        if player.drawn_cards:
            actions.append(2)
        if has_undesired_hand:
            actions.append(3)
        if has_undesired_drawn and has_undesired_hand:
            actions.append(4)
        if player.drawn_cards and has_undesired_hand:
            actions.append(5)
        return actions

    @staticmethod
    def _legal_trade_plant(player: PlayerDto, card_type: str) -> List[int]:
        actions = []
        for fi, f in enumerate(player.fields[:2]):
            if not f.card or f.card[0].type == card_type:
                actions.append(fi)
        if not actions:
            for fi, f in enumerate(player.fields[:2]):
                if BaseStrategy.can_harvest_field(player, f):
                    actions.append(2 + fi)
        return actions if actions else [0]
