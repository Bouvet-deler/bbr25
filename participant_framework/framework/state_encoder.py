"""
State encoder: converts game state into a fixed-size float vector for ML models.

Provides two entry points:
  - encode_state(env, player_idx)     — for the offline simulator during training
  - encode_live_state(game_state, player, phase_idx) — for live server play

Both produce identical 75-element vectors so that models trained offline
work directly against the live server.

Vector Layout (75 features):
  ┌──────────┬──────────────────────────────────────────────────────────────┐
  │ [0..21]  │ Own fields (2 × 11):                                         │
  │          │   one-hot card type (8) + count (1) + harvest value (1)      │
  │          │   + distance to next threshold (1)                           │
  │ [22..29] │ Hand card type counts (8)                                    │
  │ [30]     │ Hand size                                                    │
  │ [31..38] │ Drawn card type counts (8)                                   │
  │ [39..46] │ Traded card type counts (8)                                  │
  │ [47]     │ Deck size (fraction of 104)                                  │
  │ [48]     │ Round number                                                 │
  │ [49]     │ Own coins                                                    │
  │ [50..52] │ Opponent coins (up to 3)                                     │
  │ [53..56] │ Phase one-hot (4 phases)                                     │
  │ [57..64] │ Opponent fields (up to 2 opponents × 2 fields × 2 features)  │
  │ [65..72] │ (continued)                                                  │
  │ [73]     │ Is last round flag                                           │
  │ [74]     │ Deck urgency (how depleted the deck is in the last round)    │
  └──────────┴──────────────────────────────────────────────────────────────┘

All values are normalized to roughly [0, 1].
"""
from __future__ import annotations

import numpy as np

from .card_config import NUM_CARD_TYPES, TOTAL_CARDS, NAME_TO_INDEX, harvest_value, next_threshold

STATE_SIZE = 75

# Normalization constants
MAX_FIELD_SIZE = 20
MAX_COINS = 30
MAX_ROUNDS = 80
MAX_HAND = 20


def encode_state(env, player_idx: int) -> np.ndarray:
    """Encode simulator state from the perspective of ``player_idx``.

    Used during offline training with BonanzhaEnv.
    """
    vec = np.zeros(STATE_SIZE, dtype=np.float32)
    player = env.players[player_idx]
    offset = 0

    # ── Own fields (2 × 11 = 22) ────────────────────────────────────
    for fi in range(2):
        f = player.fields[fi]
        if f:
            card_type = f[0]
            idx = NAME_TO_INDEX.get(card_type, 0)
            vec[offset + idx] = 1.0  # one-hot
            count = len(f)
            vec[offset + 8] = min(count / MAX_FIELD_SIZE, 1.0)
            vec[offset + 9] = harvest_value(card_type, count) / 4.0
            nt = next_threshold(card_type, count)
            if nt is not None:
                vec[offset + 10] = min((nt - count) / 10.0, 1.0)
            else:
                vec[offset + 10] = 0.0
        offset += 11

    # ── Hand type counts (8) + size (1) = 9 ─────────────────────────
    hand_counts = _type_counts_from_names(player.hand)
    vec[offset:offset + NUM_CARD_TYPES] = hand_counts / max(MAX_HAND, 1)
    offset += NUM_CARD_TYPES
    vec[offset] = min(len(player.hand) / MAX_HAND, 1.0)
    offset += 1

    # ── Drawn card type counts (8) ──────────────────────────────────
    drawn_counts = _type_counts_from_names(player.drawn_cards)
    vec[offset:offset + NUM_CARD_TYPES] = drawn_counts / 2.0   # max 2 drawn per turn
    offset += NUM_CARD_TYPES

    # ── Traded card type counts (8) ───────────────────────────────
    traded_counts = _type_counts_from_names(player.traded_cards)
    vec[offset:offset + NUM_CARD_TYPES] = traded_counts / max(MAX_HAND, 1)
    offset += NUM_CARD_TYPES

    # ── Global features ─────────────────────────────────────────────
    vec[offset] = min(len(env.deck) / TOTAL_CARDS, 1.0)
    offset += 1
    vec[offset] = min(env.round / MAX_ROUNDS, 1.0)
    offset += 1
    vec[offset] = min(player.coins / MAX_COINS, 1.0)
    offset += 1

    # ── Opponent coins (up to 3) ────────────────────────────────────
    opp_coins = [p.coins for i, p in enumerate(env.players) if i != player_idx and p.is_active]
    for i in range(3):
        if i < len(opp_coins):
            vec[offset + i] = min(opp_coins[i] / MAX_COINS, 1.0)
    offset += 3

    # ── Phase one-hot (4) ───────────────────────────────────────────
    phase_idx = int(env.phase)
    if 0 <= phase_idx < 4:
        vec[offset + phase_idx] = 1.0
    offset += 4

    # ── Opponent field summaries (8) ─────────────────────────────────
    opp_fields = []
    for i, p in enumerate(env.players):
        if i != player_idx and p.is_active:
            for fi in range(2):
                f = p.fields[fi]
                if f:
                    opp_fields.append((NAME_TO_INDEX.get(f[0], 0) / NUM_CARD_TYPES, len(f) / MAX_FIELD_SIZE))
                else:
                    opp_fields.append((0.0, 0.0))
            if len(opp_fields) >= 4:
                break
    for i in range(min(4, len(opp_fields))):
        vec[offset + i * 2] = opp_fields[i][0]
        vec[offset + i * 2 + 1] = opp_fields[i][1]
    offset += 8

    # ── End-of-game urgency (2) ──────────────────────────────────────
    is_last_round = 1.0 if env.round >= 2 else 0.0
    vec[offset] = is_last_round
    offset += 1
    if is_last_round:
        one_round_cards = len(env.players) * 5
        vec[offset] = max(0.0, min(1.0, 1.0 - len(env.deck) / max(one_round_cards, 1)))
    offset += 1

    return vec


def encode_live_state(game_state, player, phase_idx: int) -> np.ndarray:
    """Encode live server GameStateDto into the same vector format as training.

    Parameters
    ----------
    game_state : GameStateDto
        The game state from the server (includes your_hand).
    player : PlayerDto
        The player whose perspective to encode.
    phase_idx : int
        Current phase as integer: 0=Planting, 1=PlantingOptional, 2=Trading, 3=TradePlanting.
    """
    vec = np.zeros(STATE_SIZE, dtype=np.float32)
    offset = 0

    # ── Own fields (2 × 11 = 22) ────────────────────────────────────
    for fi, field in enumerate(player.fields[:2]):
        if field.card:
            ct_name = field.card[0].type
            idx = NAME_TO_INDEX.get(ct_name, 0)
            vec[offset + idx] = 1.0
            count = len(field.card)
            vec[offset + 8] = min(count / MAX_FIELD_SIZE, 1.0)
            vec[offset + 9] = harvest_value(ct_name, count) / 4.0
            nt = next_threshold(ct_name, count)
            if nt is not None:
                vec[offset + 10] = min((nt - count) / 10.0, 1.0)
        offset += 11

    # ── Hand type counts (8) + size (1) ─────────────────────────────
    hand_cards = game_state.your_hand or []
    for c in hand_cards:
        idx = NAME_TO_INDEX.get(c.type)
        if idx is not None:
            vec[offset + idx] += 1.0 / MAX_HAND
    offset += NUM_CARD_TYPES
    vec[offset] = min(len(hand_cards) / MAX_HAND, 1.0)
    offset += 1

    # ── Drawn cards (8) ─────────────────────────────────────────────
    for c in player.drawn_cards:
        idx = NAME_TO_INDEX.get(c.type)
        if idx is not None:
            vec[offset + idx] += 1.0
    offset += NUM_CARD_TYPES

    # ── Traded cards (8) ─────────────────────────────────────────────
    for c in player.traded_cards:
        idx = NAME_TO_INDEX.get(c.type)
        if idx is not None:
            vec[offset + idx] += 1.0
    offset += NUM_CARD_TYPES

    # ── Global features ─────────────────────────────────────────────
    vec[offset] = min(game_state.deck / TOTAL_CARDS, 1.0)
    offset += 1
    vec[offset] = min(game_state.round / MAX_ROUNDS, 1.0)
    offset += 1
    vec[offset] = min(player.coins / MAX_COINS, 1.0)
    offset += 1

    # ── Opponent coins (up to 3) ────────────────────────────────────
    opp_coins = [p.coins for p in game_state.players if p.name != player.name and p.is_active]
    for i in range(3):
        if i < len(opp_coins):
            vec[offset + i] = min(opp_coins[i] / MAX_COINS, 1.0)
    offset += 3

    # ── Phase one-hot (4) ───────────────────────────────────────────
    if 0 <= phase_idx < 4:
        vec[offset + phase_idx] = 1.0
    offset += 4

    # ── Opponent fields (8) ──────────────────────────────────────────
    opp_fields = []
    for p in game_state.players:
        if p.name != player.name and p.is_active:
            for fi_o in range(min(2, len(p.fields))):
                f = p.fields[fi_o]
                if f.card:
                    opp_fields.append((
                        NAME_TO_INDEX.get(f.card[0].type, 0) / NUM_CARD_TYPES,
                        len(f.card) / MAX_FIELD_SIZE,
                    ))
                else:
                    opp_fields.append((0.0, 0.0))
            if len(opp_fields) >= 4:
                break
    for i in range(min(4, len(opp_fields))):
        vec[offset + i * 2] = opp_fields[i][0]
        vec[offset + i * 2 + 1] = opp_fields[i][1]
    offset += 8

    # ── End-of-game urgency (2) ──────────────────────────────────────
    is_last_round = 1.0 if game_state.round >= 2 else 0.0
    vec[offset] = is_last_round
    offset += 1
    if is_last_round:
        num_players = len(game_state.players)
        one_round_cards = num_players * 5
        vec[offset] = max(0.0, min(1.0, 1.0 - game_state.deck / max(one_round_cards, 1)))
    offset += 1

    return vec


# ── Helpers ──────────────────────────────────────────────────────────

def _type_counts_from_names(cards) -> np.ndarray:
    """Count occurrences of each card type in a sequence of type-name strings."""
    counts = np.zeros(NUM_CARD_TYPES, dtype=np.float32)
    for name in cards:
        idx = NAME_TO_INDEX.get(name)
        if idx is not None:
            counts[idx] += 1.0
    return counts


# Phase name string → index mapping (for convenience)
PHASE_NAME_TO_IDX = {
    "Planting": 0,
    "PlantingOptional": 1,
    "Trading": 2,
    "TradePlanting": 3,
}
