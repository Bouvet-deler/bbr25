"""
RL-based game strategy that plugs into the existing PlayerAgent architecture.

Translates live server GameStateDto → observation vector, uses the trained
DQN model to pick actions, then executes them via the API client.

Drop-in replacement for the rule-based GameStrategy.
"""
from __future__ import annotations

import logging
import random
from collections import deque
from pathlib import Path
from typing import List

import numpy as np

# Reuse the existing API client and data objects from example_client
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "example_client"))

from game_objects import FieldDto, GameStateDto, HandCardDto, PlayerDto, CardDto
from game_api_client import GameApiClient

from card_config import NUM_CARD_TYPES, NAME_TO_INDEX, harvest_value, TOTAL_CARDS
from state_encoder import STATE_SIZE
from dqn_agent import DQNAgent


class RLStrategy:
    """Game strategy powered by a trained DQN agent.

    Has the same public interface as the rule-based GameStrategy so that
    PlayerAgent can call planting_strategy(), optional_planting_strategy(),
    trading_strategy(), trade_planting_strategy(), and optional_trading_strategy()
    identically.
    """

    def __init__(self, api: GameApiClient, model_path: str = "models/best.pt") -> None:
        self.logger = logging.getLogger(f"RLStrategy.{api.game_name}")
        self.api = api

        self.agent = DQNAgent(action_dim=6, hidden=128)
        model_file = Path(model_path)
        if model_file.exists():
            self.agent.load(model_file)
            self.agent.eps = 0.0  # pure exploitation
            self.logger.info(f"Loaded RL model from {model_file}")
        else:
            self.logger.warning(f"No model at {model_file}, using random actions")
            self.agent.eps = 1.0

    # ── State encoding from live server DTOs ─────────────────────────

    def _encode_live_state(
        self,
        game_state: GameStateDto,
        player: PlayerDto,
        phase_idx: int,
    ) -> np.ndarray:
        """Encode live server state into the same vector format as training."""
        vec = np.zeros(STATE_SIZE, dtype=np.float32)
        offset = 0

        # Own fields (2 × 11 = 22)
        for fi, field in enumerate(player.fields[:2]):
            if field.card:
                ct_name = field.card[0].type
                idx = NAME_TO_INDEX.get(ct_name, 0)
                vec[offset + idx] = 1.0
                count = len(field.card)
                vec[offset + 8] = min(count / 20.0, 1.0)
                vec[offset + 9] = harvest_value(ct_name, count) / 4.0
                # Distance to next threshold
                from card_config import next_threshold
                nt = next_threshold(ct_name, count)
                if nt is not None:
                    vec[offset + 10] = min((nt - count) / 10.0, 1.0)
            offset += 11

        # Hand type counts (8) + size (1)
        hand_cards = game_state.your_hand or []
        for c in hand_cards:
            idx = NAME_TO_INDEX.get(c.type)
            if idx is not None:
                vec[offset + idx] += 1.0 / 20.0
        offset += NUM_CARD_TYPES
        vec[offset] = min(len(hand_cards) / 20.0, 1.0)
        offset += 1

        # Drawn cards (8)
        for c in player.drawn_cards:
            idx = NAME_TO_INDEX.get(c.type)
            if idx is not None:
                vec[offset + idx] += 1.0
        offset += NUM_CARD_TYPES

        # Traded cards (8)
        for c in player.traded_cards:
            idx = NAME_TO_INDEX.get(c.type)
            if idx is not None:
                vec[offset + idx] += 1.0
        offset += NUM_CARD_TYPES

        # Global
        vec[offset] = min(game_state.deck / TOTAL_CARDS, 1.0)
        offset += 1
        vec[offset] = min(game_state.round / 80.0, 1.0)
        offset += 1
        vec[offset] = min(player.coins / 30.0, 1.0)
        offset += 1

        # Opponent coins (up to 3)
        opp_coins = [p.coins for p in game_state.players if p.name != player.name and p.is_active]
        for i in range(3):
            if i < len(opp_coins):
                vec[offset + i] = min(opp_coins[i] / 30.0, 1.0)
        offset += 3

        # Phase one-hot
        if 0 <= phase_idx < 4:
            vec[offset + phase_idx] = 1.0
        offset += 4

        # Opponent fields
        opp_fields = []
        for p in game_state.players:
            if p.name != player.name and p.is_active:
                for fi_o in range(min(2, len(p.fields))):
                    f = p.fields[fi_o]
                    if f.card:
                        opp_fields.append((
                            NAME_TO_INDEX.get(f.card[0].type, 0) / NUM_CARD_TYPES,
                            len(f.card) / 20.0,
                        ))
                    else:
                        opp_fields.append((0.0, 0.0))
                if len(opp_fields) >= 4:
                    break
        for i in range(min(4, len(opp_fields))):
            vec[offset + i * 2] = opp_fields[i][0]
            vec[offset + i * 2 + 1] = opp_fields[i][1]
        offset += 8

        # End-of-game urgency (2) — must match state_encoder.py layout
        is_last_round = 1.0 if game_state.round >= 2 else 0.0
        vec[offset] = is_last_round
        offset += 1
        if is_last_round:
            num_players = len(game_state.players)
            one_round_cards = num_players * 5
            vec[offset] = max(0.0, min(1.0, 1.0 - game_state.deck / max(one_round_cards, 1)))
        offset += 1

        return vec

    # ── Legal action helpers ─────────────────────────────────────────

    @staticmethod
    def _can_harvest_field(player: PlayerDto, field: FieldDto) -> bool:
        count = len(field.card)
        if count == 0:
            return False
        if count >= 2:
            return True
        for other in player.fields:
            if other.key != field.key and len(other.card) >= 2:
                return False
        return True

    def _legal_planting(self, player: PlayerDto, hand: list) -> list[int]:
        if not hand:
            return [0]
        card_type = hand[0].type
        actions = []
        for fi, f in enumerate(player.fields[:2]):
            if not f.card or f.card[0].type == card_type:
                actions.append(fi)
        if not actions:
            for fi, f in enumerate(player.fields[:2]):
                if self._can_harvest_field(player, f):
                    actions.append(3 + fi)
        return actions if actions else [0]

    def _legal_optional(self, player: PlayerDto, hand: list) -> list[int]:
        actions = [2]  # skip
        if not hand:
            return actions
        card_type = hand[0].type
        for fi, f in enumerate(player.fields[:2]):
            if not f.card or f.card[0].type == card_type:
                actions.append(fi)
        for fi, f in enumerate(player.fields[:2]):
            if f.card and f.card[0].type != card_type and self._can_harvest_field(player, f):
                actions.append(3 + fi)
        return actions

    def _legal_trading(self, player: PlayerDto, hand_cards: list) -> list[int]:
        actions = [0]  # skip always legal
        owned_types = {f.card[0].type for f in player.fields if f.card}
        has_undesired_drawn = any(c.type not in owned_types for c in player.drawn_cards)
        has_undesired_hand = any(c.type not in owned_types for c in hand_cards)

        if has_undesired_drawn:
            actions.append(1)  # offer undesired drawn
        if player.drawn_cards:
            actions.append(2)  # offer all drawn
        if has_undesired_hand:
            actions.append(3)  # offer 1 undesired hand card
        if has_undesired_drawn and has_undesired_hand:
            actions.append(4)  # drawn + hand
        if player.drawn_cards and has_undesired_hand:
            actions.append(5)  # all drawn + hand
        return actions

    def _legal_trade_plant(self, player: PlayerDto, card_type: str) -> list[int]:
        actions = []
        for fi, f in enumerate(player.fields[:2]):
            if not f.card or f.card[0].type == card_type:
                actions.append(fi)
        if not actions:
            for fi, f in enumerate(player.fields[:2]):
                if self._can_harvest_field(player, f):
                    actions.append(2 + fi)
        return actions if actions else [0]

    # ── Harvest value helper ─────────────────────────────────────────

    @staticmethod
    def _harvest_value(field: FieldDto) -> int:
        num = len(field.card)
        if num == 0:
            return 0
        for entry in field.card[0].exchange_map:
            if num >= entry.crop_size:
                return entry.value
        return 0

    # ── Display helpers (same as rule-based) ─────────────────────────

    @staticmethod
    def _fmt_hand(cards) -> str:
        if not cards:
            return "(empty)"
        from collections import Counter
        counts = Counter(c.type for c in cards)
        return ", ".join(f"{t}×{n}" if n > 1 else t for t, n in counts.items())

    @staticmethod
    def _fmt_fields(fields: list[FieldDto]) -> str:
        parts = []
        for i, f in enumerate(fields, 1):
            if f.card:
                parts.append(f"Field {i}: {f.card[0].type}×{len(f.card)}")
            else:
                parts.append(f"Field {i}: empty")
        return "  |  ".join(parts)

    # ── Phase strategies (public API matching GameStrategy) ──────────

    def planting_strategy(self, game_state: GameStateDto, current_player: PlayerDto, player_id: str) -> None:
        cards_in_hand = self.api.get_game(player_id=player_id).your_hand
        if not cards_in_hand:
            self.api.end_planting(player_id)
            return

        print(f"  [RL] Hand ({len(cards_in_hand)}): {self._fmt_hand(cards_in_hand)}")
        print(f"  [RL] Fields: {self._fmt_fields(current_player.fields)}")

        obs = self._encode_live_state(game_state, current_player, phase_idx=0)
        legal = self._legal_planting(current_player, cards_in_hand)
        action = self.agent.select_action_greedy(obs, legal)

        card_type = cards_in_hand[0].type

        if action in (0, 1):
            field = current_player.fields[action]
            if field.card and field.card[0].type != card_type:
                if self._can_harvest_field(current_player, field):
                    self.api.harvest_field(player_id, field.key)
                    print(f"  [RL] Harvested Field {action + 1}")
                else:
                    action = self._legal_planting(current_player, cards_in_hand)[0]
            self.api.plant(player_id, current_player.fields[action if action in (0, 1) else 0].key)
            print(f"  [RL] Planted {card_type} on Field {action + 1}")

        elif action in (3, 4):
            fi = action - 3
            if self._can_harvest_field(current_player, current_player.fields[fi]):
                self.api.harvest_field(player_id, current_player.fields[fi].key)
                print(f"  [RL] Harvested Field {fi + 1}")
            self.api.plant(player_id, current_player.fields[fi].key)
            print(f"  [RL] Planted {card_type} on Field {fi + 1}")

        # Refresh fields
        fresh = self.api.get_game(player_id=player_id)
        fresh_p = next((p for p in fresh.players if p.name == current_player.name), current_player)
        current_player.fields = fresh_p.fields
        print(f"  [RL] Fields after: {self._fmt_fields(current_player.fields)}")

    def optional_planting_strategy(self, game_state: GameStateDto, current_player: PlayerDto, player_id: str) -> None:
        fresh_state = self.api.get_game(player_id=player_id)
        cards_in_hand = fresh_state.your_hand
        if not cards_in_hand:
            self.api.end_planting(player_id)
            return

        fresh_player = next((p for p in fresh_state.players if p.name == current_player.name), current_player)
        obs = self._encode_live_state(fresh_state, fresh_player, phase_idx=1)
        legal = self._legal_optional(fresh_player, cards_in_hand)
        action = self.agent.select_action_greedy(obs, legal)

        card_type = cards_in_hand[0].type

        if action == 2:
            print(f"  [RL] Skipping optional plant")
            self.api.end_planting(player_id)
            return

        if action in (0, 1):
            f = fresh_player.fields[action]
            if f.card and f.card[0].type != card_type:
                self.api.end_planting(player_id)
                return
            self.api.plant(player_id, f.key)
            print(f"  [RL] Optional-planted {card_type} on Field {action + 1}")

        elif action in (3, 4):
            fi = action - 3
            if self._can_harvest_field(fresh_player, fresh_player.fields[fi]):
                self.api.harvest_field(player_id, fresh_player.fields[fi].key)
            self.api.plant(player_id, fresh_player.fields[fi].key)
            print(f"  [RL] Optional-planted {card_type} on Field {fi + 1}")

        updated = self.api.get_game(player_id=player_id)
        refreshed = next((p for p in updated.players if p.name == current_player.name), None)
        if refreshed:
            current_player.fields = refreshed.fields
        print(f"  [RL] Fields after: {self._fmt_fields(current_player.fields)}")

    def trading_strategy(self, game_state: GameStateDto, current_player: PlayerDto, player_id: str) -> None:
        """Post a trade offer using RL-selected action.

        Action space mirrors the simulator:
          0 = skip, 1 = undesired drawn, 2 = all drawn,
          3 = 1 undesired hand card, 4 = drawn + hand, 5 = all drawn + hand
        """
        turned_over = list(current_player.drawn_cards)[:2]
        cards_in_hand = self.api.get_game(player_id=player_id).your_hand

        print(f"  [RL] Fields: {self._fmt_fields(current_player.fields)}")
        print(f"  [RL] Drawn: {self._fmt_hand(turned_over)}")
        print(f"  [RL] Hand ({len(cards_in_hand)}): {self._fmt_hand(cards_in_hand)}")

        obs = self._encode_live_state(game_state, current_player, phase_idx=2)
        legal = self._legal_trading(current_player, cards_in_hand)
        action = self.agent.select_action_greedy(obs, legal)

        owned_types = {f.card[0].type for f in current_player.fields if f.card}

        if action == 0:
            print(f"  [RL] Skipping trade")
            self.api.end_trading(player_id)
            return

        # Build offer based on action
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
            print(f"  [RL] Offering [{offer_str}] for any {desired_types}")
            import time
            time.sleep(5)
        except Exception as e:
            self.logger.error(f"Trade offer error: {e}")

        self.api.end_trading(player_id)

    def trade_planting_strategy(self, game_state: GameStateDto, current_player: PlayerDto, player_id: str) -> None:
        """Plant all traded/drawn cards using RL decisions."""
        remaining = list(current_player.traded_cards)
        if current_player.name == game_state.current_player:
            remaining += current_player.drawn_cards[:2]

        if not remaining:
            print(f"  [RL] No cards to trade-plant")
            return

        print(f"  [RL] Must plant: {self._fmt_hand(remaining)}")

        for card in remaining:
            fresh = self.api.get_game(player_id=player_id)
            fresh_p = next((p for p in fresh.players if p.name == current_player.name), current_player)

            obs = self._encode_live_state(fresh, fresh_p, phase_idx=3)
            legal = self._legal_trade_plant(fresh_p, card.type)
            action = self.agent.select_action_greedy(obs, legal)

            if action in (0, 1):
                f = fresh_p.fields[action]
                if f.card and f.card[0].type != card.type:
                    if self._can_harvest_field(fresh_p, f):
                        self.api.harvest_field(player_id, f.key)
                self.api.trade_plant(player_id, card.id, f.key)
                print(f"  [RL] Trade-planted {card.type} on Field {action + 1}")

            elif action in (2, 3):
                fi = action - 2
                if self._can_harvest_field(fresh_p, fresh_p.fields[fi]):
                    self.api.harvest_field(player_id, fresh_p.fields[fi].key)
                self.api.trade_plant(player_id, card.id, fresh_p.fields[fi].key)
                print(f"  [RL] Trade-planted {card.type} on Field {fi + 1}")

        final = self.api.get_game(player_id=player_id)
        final_p = next((p for p in final.players if p.name == current_player.name), None)
        if final_p:
            print(f"  [RL] Fields after: {self._fmt_fields(final_p.fields)}")

    def last_round_harvest_strategy(
        self,
        game_state: GameStateDto,
        current_player: PlayerDto,
        player_id: str,
    ) -> None:
        """Harvest all harvestable fields when the deck is nearly empty.

        Only fires on the last deck pass (round == 2) when fewer than
        one full round of cards remains (num_players * 5 cards per round).
        Called at the end of TradePlanting so coins aren't lost if the
        server ends the game before the player can act again.
        """
        num_players = len(game_state.players)
        last_round_threshold = num_players * 5
        if game_state.round < 2 or game_state.deck > last_round_threshold:
            return

        print(f"  [RL] ⚠ Last deck pass, {game_state.deck} cards left — performing end-of-game harvest")
        fresh_state = self.api.get_game(player_id=player_id)
        fresh_player = next(
            (p for p in fresh_state.players if p.name == current_player.name),
            current_player,
        )

        harvested_any = False
        for field in list(fresh_player.fields):
            if field.card and self._can_harvest_field(fresh_player, field):
                coins = self._harvest_value(field)
                try:
                    self.api.harvest_field(player_id, field.key)
                except Exception:
                    # Game may have ended server-side between phases; silently stop
                    break
                print(f"  [RL] Harvested {len(field.card)}×{field.card[0].type} → +{coins} (end-of-game)")
                harvested_any = True
                # Refresh so bean-protection rule re-evaluates after each harvest
                fresh_state = self.api.get_game(player_id=player_id)
                fresh_player = next(
                    (p for p in fresh_state.players if p.name == current_player.name),
                    fresh_player,
                )
                if not fresh_player:
                    break

        if harvested_any:
            print(f"  [RL] Fields after end-of-game harvest: {self._fmt_fields(fresh_player.fields)}")

    def optional_trading_strategy(self, game_state: GameStateDto, current_player: PlayerDto, player_id: str) -> None:
        """Evaluate and potentially accept trades from other players.
        Uses a simple heuristic similar to the rule-based version, since
        the RL model focuses on planting/harvesting decisions."""
        posted_trades = game_state.available_trades
        if not posted_trades:
            return

        owned_types = {f.card[0].type for f in current_player.fields if f.card}

        for trade in posted_trades:
            wanted = [t for t in trade.offered_cards if t in owned_types]
            if not wanted:
                continue

            matching = [c for c in game_state.your_hand if c.type in trade.card_types_wanted]
            if not matching:
                continue

            from collections import Counter
            counts = Counter(c.type for c in matching)
            best_type = max(counts, key=counts.get)
            card_to_give = next(c for c in matching if c.type == best_type)

            try:
                self.api.accept_trade(player_id, trade.negotiation_id, [card_to_give.id])
                print(f"  [RL] 🤝 Accepted trade: gave {card_to_give.type}, received {wanted}")
                return
            except Exception as e:
                if "404" not in str(e):
                    self.logger.error(f"Trade accept error: {e}")
