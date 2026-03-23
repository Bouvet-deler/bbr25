"""
Local Bonanzha game simulator as a Gymnasium-style environment.

This mirrors the server logic from Game.cs so that we can train RL agents
entirely offline without needing the C# server running.

The environment manages a full N-player game but exposes the perspective
of a single "learning agent" (player index 0) while other players use
a supplied policy callback.

Action encoding per phase
--------------------------
Planting / PlantingOptional:
  0 = plant on field 0
  1 = plant on field 1
  2 = skip / end planting  (only valid in PlantingOptional)
  3 = harvest field 0 then plant
  4 = harvest field 1 then plant

Trading (active player can offer drawn cards AND/OR hand cards):
  0 = skip trading (end trading immediately)
  1 = offer undesired drawn cards (drawn cards not matching owned fields)
  2 = offer ALL drawn cards
  3 = offer 1 undesired hand card (hand card not matching owned fields)
  4 = offer undesired drawn cards + 1 undesired hand card
  5 = offer all drawn cards + 1 undesired hand card

TradePlanting (called once per card to place):
  0 = place on field 0
  1 = place on field 1
  2 = harvest field 0 then place
  3 = harvest field 1 then place
"""
from __future__ import annotations

import random
from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field as dc_field
from enum import IntEnum
from typing import Callable, List, Optional, Tuple

import gymnasium as gym
import numpy as np

from card_config import (
    CARD_TYPES,
    NUM_CARD_TYPES,
    TOTAL_CARDS,
    NAME_TO_INDEX,
    NAME_TO_CARD_TYPE,
    harvest_value,
)
from state_encoder import encode_state, STATE_SIZE


class Phase(IntEnum):
    PLANTING = 0
    PLANTING_OPTIONAL = 1
    TRADING = 2
    TRADE_PLANTING = 3


@dataclass
class PlayerState:
    """Mutable per-player state inside the simulator."""
    name: str
    hand: deque  # deque of card-type names (str)
    fields: List[List[str]]  # 2 fields, each a list of card-type names
    traded_cards: List[str]
    drawn_cards: List[str]
    coins: int = 0
    is_active: bool = True


class BonanzhaEnv(gym.Env):
    """Local Bonanzha game simulator.

    Parameters
    ----------
    num_players : int
        Number of players (2-5).
    opponent_policy : callable
        ``opponent_policy(obs, legal_actions, phase) -> action_index``
        Called for every non-learning player decision. If ``None``, random
        legal actions are chosen.
    max_deck_reshuffles : int
        Game ends after the deck is reshuffled this many times (server default=2).
    """

    metadata = {"render_modes": []}

    # Actions per phase (max)
    MAX_PLANT_ACTIONS = 5       # field0, field1, skip, harvest0+plant, harvest1+plant
    MAX_TRADE_ACTIONS = 6       # skip, undesired_drawn, all_drawn, hand_card, drawn+hand, all_drawn+hand
    MAX_TRADE_PLANT_ACTIONS = 4 # field0, field1, harvest0, harvest1

    def __init__(
        self,
        num_players: int = 4,
        opponent_policy: Optional[Callable] = None,
        max_deck_reshuffles: int = 2,
    ):
        super().__init__()
        self.num_players = num_players
        self.opponent_policy = opponent_policy or self._random_policy
        self.max_deck_reshuffles = max_deck_reshuffles

        self.observation_space = gym.spaces.Box(
            low=-1.0, high=1.0, shape=(STATE_SIZE,), dtype=np.float32,
        )
        # We use the largest action count; masking handles validity
        self.action_space = gym.spaces.Discrete(self.MAX_TRADE_ACTIONS)

        # Will be set in reset()
        self.players: List[PlayerState] = []
        self.deck: List[str] = []
        self.discard: List[str] = []
        self.current_player_idx: int = 0
        self.phase: Phase = Phase.PLANTING
        self.reshuffles: int = 0
        self.game_over: bool = False
        self.round: int = 0

    # ── Gymnasium interface ──────────────────────────────────────────

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._init_game()
        obs = self._get_obs()
        info = {"legal_actions": self._legal_actions(), "phase": int(self.phase)}
        # If it's not the learning agent's turn, simulate opponents until it is
        self._play_until_agent_turn()
        obs = self._get_obs()
        info = {"legal_actions": self._legal_actions(), "phase": int(self.phase)}
        return obs, info

    def step(self, action: int):
        """Execute the learning agent's action and then simulate opponents
        until the agent needs to act again (or the game ends)."""
        if self.game_over:
            obs = self._get_obs()
            return obs, 0.0, True, False, {}

        reward = self._execute_action(0, action)

        # Now simulate all other players / phases until it's agent's turn again
        self._play_until_agent_turn()

        obs = self._get_obs()
        terminated = self.game_over
        info = {"legal_actions": self._legal_actions(), "phase": int(self.phase)}

        if terminated:
            # Harvest all remaining fields for all players (mirrors server HandleGameEnd)
            for p in self.players:
                for fi in range(len(p.fields)):
                    if p.fields[fi]:
                        self._harvest(p, fi)

            agent_coins = self.players[0].coins
            all_coins = [p.coins for p in self.players]
            avg_all = sum(all_coins) / len(all_coins)

            # Rank: 0 = 1st, 1 = 2nd, etc. (ties resolved by counting strictly better players)
            rank = sum(1 for c in all_coins if c > agent_coins)

            # Placement bonus: winning is the primary objective
            placement_bonuses = [3.0, 0.5, -0.5, -2.0, -3.0]
            placement_reward = placement_bonuses[min(rank, len(placement_bonuses) - 1)]

            # Coin margin: continuous incentive to maximise coins regardless of rank
            margin_reward = (agent_coins - avg_all) * 0.3

            reward += placement_reward + margin_reward

        return obs, reward, terminated, False, info

    # ── Game initialisation ──────────────────────────────────────────

    def _init_game(self):
        self.game_over = False
        self.reshuffles = 0
        self.round = 0

        # Build deck
        self.discard = []
        deck = []
        for ct in CARD_TYPES:
            deck.extend([ct.name] * ct.count)
        random.shuffle(deck)
        self.deck = deck

        # Create players
        self.players = []
        for i in range(self.num_players):
            p = PlayerState(
                name=f"Player{i}",
                hand=deque(),
                fields=[[], []],
                traded_cards=[],
                drawn_cards=[],
            )
            # Deal 5 cards
            for _ in range(5):
                card = self._draw_card()
                if card is not None:
                    p.hand.append(card)
            self.players.append(p)

        self.current_player_idx = 0
        self.phase = Phase.PLANTING

    # ── Card drawing ─────────────────────────────────────────────────

    def _draw_card(self) -> Optional[str]:
        """Draw a card from the deck, reshuffling discard if needed."""
        if not self.deck:
            self.reshuffles += 1
            if self.reshuffles > self.max_deck_reshuffles:
                self.game_over = True
                return None
            self.deck = list(self.discard)
            self.discard = []
            random.shuffle(self.deck)
            if not self.deck:
                self.game_over = True
                return None
        return self.deck.pop()

    # ── Harvest logic ────────────────────────────────────────────────

    def _can_harvest(self, player: PlayerState, field_idx: int) -> bool:
        """Bean protection rule: can't harvest 1-card field if another has 2+."""
        f = player.fields[field_idx]
        if len(f) == 0:
            return False
        if len(f) >= 2:
            return True
        # Exactly 1 card — only if no other field has 2+
        for i, other in enumerate(player.fields):
            if i != field_idx and len(other) >= 2:
                return False
        return True

    def _harvest(self, player: PlayerState, field_idx: int) -> int:
        """Harvest a field. Returns coins earned."""
        f = player.fields[field_idx]
        if not f:
            return 0
        card_type = f[0]
        num_cards = len(f)
        coins = harvest_value(card_type, num_cards)
        player.coins += coins
        # Remaining cards go to discard
        cards_to_discard = max(0, num_cards - coins)
        self.discard.extend([card_type] * cards_to_discard)
        player.fields[field_idx] = []
        return coins

    # ── Planting ─────────────────────────────────────────────────────

    def _plant_card(self, player: PlayerState, card: str, field_idx: int) -> bool:
        """Plant a card on a field. Returns True if successful."""
        f = player.fields[field_idx]
        if f and f[0] != card:
            return False  # Field has different type
        f.append(card)
        return True

    # ── Action execution ─────────────────────────────────────────────

    def _execute_action(self, player_idx: int, action: int) -> float:
        """Execute an action for the given player. Returns immediate reward."""
        player = self.players[player_idx]
        reward = 0.0

        if self.phase == Phase.PLANTING:
            reward = self._execute_planting(player, action)
        elif self.phase == Phase.PLANTING_OPTIONAL:
            reward = self._execute_planting_optional(player, action)
        elif self.phase == Phase.TRADING:
            reward = self._execute_trading(player, action)
        elif self.phase == Phase.TRADE_PLANTING:
            reward = self._execute_trade_planting(player, action)

        return reward

    def _execute_planting(self, player: PlayerState, action: int) -> float:
        """Planting phase: must plant the first card from hand."""
        if not player.hand:
            self._go_to_trading()
            return 0.0

        card = player.hand[0]  # peek
        reward = 0.0

        if action in (0, 1):
            field_idx = action
            f = player.fields[field_idx]
            if f and f[0] != card:
                # Invalid: field has different type → harvest first if legal
                if self._can_harvest(player, field_idx):
                    reward += self._harvest(player, field_idx) * 0.1
                else:
                    # Pick the first valid field instead (fallback)
                    field_idx = self._find_valid_field(player, card)
                    if field_idx is None:
                        self._go_to_trading()
                        return -0.5
            player.hand.popleft()
            self._plant_card(player, card, field_idx)

        elif action == 3:  # harvest field 0 then plant
            if self._can_harvest(player, 0):
                reward += self._harvest(player, 0) * 0.1
            player.hand.popleft()
            self._plant_card(player, card, 0)

        elif action == 4:  # harvest field 1 then plant
            if self._can_harvest(player, 1):
                reward += self._harvest(player, 1) * 0.1
            player.hand.popleft()
            self._plant_card(player, card, 1)

        else:
            # Invalid action for planting; default to first valid field
            field_idx = self._find_valid_field(player, card)
            if field_idx is not None:
                player.hand.popleft()
                self._plant_card(player, card, field_idx)
            else:
                self._go_to_trading()
                return -0.5

        # Transition
        if player.hand:
            self.phase = Phase.PLANTING_OPTIONAL
        else:
            self._go_to_trading()
        return reward

    def _execute_planting_optional(self, player: PlayerState, action: int) -> float:
        """Optional second planting."""
        if not player.hand:
            self._go_to_trading()
            return 0.0

        card = player.hand[0]

        if action == 2:  # skip
            self._go_to_trading()
            return 0.0

        reward = 0.0
        if action in (0, 1):
            field_idx = action
            f = player.fields[field_idx]
            if f and f[0] != card:
                # Can't plant here without harvesting; just skip
                self._go_to_trading()
                return 0.0
            player.hand.popleft()
            self._plant_card(player, card, field_idx)

        elif action == 3:
            if self._can_harvest(player, 0):
                reward += self._harvest(player, 0) * 0.1
                player.hand.popleft()
                self._plant_card(player, card, 0)
            else:
                self._go_to_trading()
                return 0.0

        elif action == 4:
            if self._can_harvest(player, 1):
                reward += self._harvest(player, 1) * 0.1
                player.hand.popleft()
                self._plant_card(player, card, 1)
            else:
                self._go_to_trading()
                return 0.0

        self._go_to_trading()
        return reward

    def _execute_trading(self, player: PlayerState, action: int) -> float:
        """Trading phase: the active player can offer drawn cards AND/OR hand cards.
        In self-play training, trades are resolved deterministically:
        an opponent accepts if the offered card matches one of their fields."""
        owned_types = {f[0] for f in player.fields if f}
        undesired_drawn = [c for c in player.drawn_cards if c not in owned_types]
        undesired_hand = [c for c in player.hand if c not in owned_types]

        # action 0 = skip
        if action == 0:
            self._go_to_trade_planting()
            return 0.0

        # Build the list of cards to offer based on action
        offered_from_drawn = []  # card type names from drawn_cards
        offered_from_hand = []   # card type names from hand

        if action == 1:    # offer undesired drawn cards
            offered_from_drawn = list(undesired_drawn)
        elif action == 2:  # offer ALL drawn cards
            offered_from_drawn = list(player.drawn_cards)
        elif action == 3:  # offer 1 undesired hand card
            offered_from_hand = list(undesired_hand[:1])
        elif action == 4:  # undesired drawn + 1 undesired hand card
            offered_from_drawn = list(undesired_drawn)
            offered_from_hand = list(undesired_hand[:1])
        elif action == 5:  # all drawn + 1 undesired hand card
            offered_from_drawn = list(player.drawn_cards)
            offered_from_hand = list(undesired_hand[:1])

        all_offered = offered_from_drawn + offered_from_hand
        if not all_offered:
            self._go_to_trade_planting()
            return 0.0

        # Try to find an opponent who can accept
        reward = 0.0
        for opp_idx in range(len(self.players)):
            if opp_idx == self.current_player_idx:
                continue
            opp = self.players[opp_idx]
            if not opp.is_active:
                continue

            # Opponent wants cards that match their fields
            opp_owned_types = {f[0] for f in opp.fields if f}
            wanted_from_offer = [c for c in all_offered if c in opp_owned_types]
            if not wanted_from_offer:
                continue

            # Opponent pays with one card matching our fields
            payment = None
            for card_name in list(opp.hand):
                if card_name in owned_types:
                    payment = card_name
                    break

            if payment is None:
                continue

            # Execute trade: transfer offered cards
            for c in wanted_from_offer:
                if c in player.drawn_cards:
                    player.drawn_cards.remove(c)
                    opp.traded_cards.append(c)
                elif c in player.hand:
                    player.hand.remove(c)
                    opp.traded_cards.append(c)

            # Payment from opponent
            opp.hand.remove(payment)
            player.traded_cards.append(payment)
            reward += 0.2  # reward for successful trade
            break

        self._go_to_trade_planting()
        return reward

    def _execute_trade_planting(self, player: PlayerState, action: int) -> float:
        """Plant one traded/drawn card. Called repeatedly until all placed."""
        cards_to_place = player.drawn_cards + player.traded_cards
        if not cards_to_place:
            return 0.0

        card = cards_to_place[0]
        reward = 0.0

        if action in (0, 1):
            field_idx = action
            f = player.fields[field_idx]
            if f and f[0] != card:
                # Need to harvest first
                if self._can_harvest(player, field_idx):
                    reward += self._harvest(player, field_idx) * 0.1
                else:
                    # Find valid field
                    field_idx = self._find_valid_field(player, card)
                    if field_idx is None:
                        # Must harvest something
                        for fi in range(2):
                            if self._can_harvest(player, fi):
                                reward += self._harvest(player, fi) * 0.1
                                field_idx = fi
                                break
                    if field_idx is None:
                        field_idx = 0  # forced
                        self._harvest(player, 0)
            self._plant_card(player, card, field_idx)

        elif action in (2, 3):
            harvest_idx = action - 2
            if self._can_harvest(player, harvest_idx):
                reward += self._harvest(player, harvest_idx) * 0.1
            self._plant_card(player, card, harvest_idx)

        else:
            field_idx = self._find_valid_field(player, card)
            if field_idx is not None:
                self._plant_card(player, card, field_idx)
            else:
                for fi in range(2):
                    if self._can_harvest(player, fi):
                        self._harvest(player, fi)
                        self._plant_card(player, card, fi)
                        break

        # Remove the card from drawn/traded
        if card in player.drawn_cards:
            player.drawn_cards.remove(card)
        elif card in player.traded_cards:
            player.traded_cards.remove(card)

        return reward

    # ── Phase transitions ────────────────────────────────────────────

    def _go_to_trading(self):
        """Transition to trading phase: draw 2 cards for current player."""
        self.phase = Phase.TRADING
        player = self.players[self.current_player_idx]
        for _ in range(2):
            card = self._draw_card()
            if card is not None:
                player.drawn_cards.append(card)

    def _go_to_trade_planting(self):
        self.phase = Phase.TRADE_PLANTING

    def _go_to_next_turn(self):
        """Draw 3 cards into current player's hand, advance to next player."""
        player = self.players[self.current_player_idx]
        for _ in range(3):
            card = self._draw_card()
            if card is not None:
                player.hand.append(card)

        self.round += 1
        # Advance to next active player
        next_idx = (self.current_player_idx + 1) % self.num_players
        attempts = 0
        while not self.players[next_idx].is_active and attempts < self.num_players:
            next_idx = (next_idx + 1) % self.num_players
            attempts += 1

        self.current_player_idx = next_idx
        self.phase = Phase.PLANTING

    # ── Opponent simulation ──────────────────────────────────────────

    def _play_until_agent_turn(self):
        """Simulate all game phases until it's the learning agent's (idx 0) turn
        and the agent needs to make a decision."""
        max_iterations = 500  # safety
        for _ in range(max_iterations):
            if self.game_over:
                return

            # If it's the agent's turn AND the phase requires a decision, return
            if self.current_player_idx == 0:
                if self.phase in (Phase.PLANTING, Phase.PLANTING_OPTIONAL, Phase.TRADING):
                    return
                if self.phase == Phase.TRADE_PLANTING:
                    player = self.players[0]
                    if player.drawn_cards or player.traded_cards:
                        return
                    # All cards placed → go to next turn
                    self._go_to_next_turn()
                    continue

            # Simulate the current player's phase
            pidx = self.current_player_idx
            player = self.players[pidx]

            if self.phase == Phase.PLANTING:
                if not player.hand:
                    self._go_to_trading()
                    continue
                action = self._opponent_action(pidx)
                self._execute_planting(player, action)

            elif self.phase == Phase.PLANTING_OPTIONAL:
                if not player.hand:
                    self._go_to_trading()
                    continue
                action = self._opponent_action(pidx)
                self._execute_planting_optional(player, action)

            elif self.phase == Phase.TRADING:
                action = self._opponent_action(pidx)
                self._execute_trading(player, action)

            elif self.phase == Phase.TRADE_PLANTING:
                # Plant all cards for current player
                self._trade_plant_all(pidx)
                # Also plant traded cards for all other players
                for other_idx in range(self.num_players):
                    if other_idx != pidx:
                        self._trade_plant_all(other_idx)
                self._go_to_next_turn()

    def _trade_plant_all(self, player_idx: int):
        """Plant all drawn + traded cards for a player using their policy."""
        player = self.players[player_idx]
        max_cards = 20  # safety
        for _ in range(max_cards):
            cards = player.drawn_cards + player.traded_cards
            if not cards:
                break
            if player_idx == 0:
                # Agent decides
                return  # will be called via step()
            action = self._opponent_action(player_idx)
            self._execute_trade_planting(player, action)

    def _opponent_action(self, player_idx: int) -> int:
        """Get an action from the opponent policy."""
        legal = self._legal_actions_for(player_idx)
        obs = self._get_obs_for(player_idx)
        return self.opponent_policy(obs, legal, int(self.phase))

    # ── Observation & legal actions ──────────────────────────────────

    def _get_obs(self) -> np.ndarray:
        return self._get_obs_for(0)

    def _get_obs_for(self, player_idx: int) -> np.ndarray:
        return encode_state(self, player_idx)

    def _legal_actions(self) -> List[int]:
        return self._legal_actions_for(0)

    def _legal_actions_for(self, player_idx: int) -> List[int]:
        player = self.players[player_idx]

        if self.phase == Phase.PLANTING:
            return self._legal_planting_actions(player)
        elif self.phase == Phase.PLANTING_OPTIONAL:
            return self._legal_optional_actions(player)
        elif self.phase == Phase.TRADING:
            return self._legal_trading_actions(player)
        elif self.phase == Phase.TRADE_PLANTING:
            return self._legal_trade_plant_actions(player)
        return [0]

    def _legal_planting_actions(self, player: PlayerState) -> List[int]:
        if not player.hand:
            return [0]
        card = player.hand[0]
        actions = []
        for fi in range(2):
            f = player.fields[fi]
            if not f or f[0] == card:
                actions.append(fi)
        if not actions:
            # Must harvest somewhere
            for fi in range(2):
                if self._can_harvest(player, fi):
                    actions.append(3 + fi)
            if not actions:
                actions = [0]  # shouldn't happen but safety
        return actions

    def _legal_optional_actions(self, player: PlayerState) -> List[int]:
        actions = [2]  # skip always legal
        if not player.hand:
            return actions
        card = player.hand[0]
        for fi in range(2):
            f = player.fields[fi]
            if not f or f[0] == card:
                actions.append(fi)
        # Also allow harvest + plant
        for fi in range(2):
            f = player.fields[fi]
            if f and f[0] != card and self._can_harvest(player, fi):
                actions.append(3 + fi)
        return actions

    def _legal_trading_actions(self, player: PlayerState) -> List[int]:
        actions = [0]  # skip always legal
        owned_types = {f[0] for f in player.fields if f}
        has_undesired_drawn = any(c not in owned_types for c in player.drawn_cards)
        has_undesired_hand = any(c not in owned_types for c in player.hand)

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

    def _legal_trade_plant_actions(self, player: PlayerState) -> List[int]:
        cards = player.drawn_cards + player.traded_cards
        if not cards:
            return [0]
        card = cards[0]
        actions = []
        for fi in range(2):
            f = player.fields[fi]
            if not f or f[0] == card:
                actions.append(fi)
        if not actions:
            for fi in range(2):
                if self._can_harvest(player, fi):
                    actions.append(2 + fi)
        if not actions:
            actions = [0]
        return actions

    # ── Utility ──────────────────────────────────────────────────────

    def _find_valid_field(self, player: PlayerState, card: str) -> Optional[int]:
        """Find a field where card can be placed without harvesting."""
        # Prefer matching field, then empty
        for fi in range(2):
            if player.fields[fi] and player.fields[fi][0] == card:
                return fi
        for fi in range(2):
            if not player.fields[fi]:
                return fi
        return None

    @staticmethod
    def _random_policy(obs, legal_actions, phase) -> int:
        return random.choice(legal_actions)
