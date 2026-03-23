"""
State encoder: converts game simulator state into a fixed-size float vector.

The encoding captures everything the learning agent can observe and is
designed to be compact but expressive enough for DQN to learn from.

Layout (per player_idx perspective):
  [0..21]   — own fields (2 × 11): one-hot card type (8) + count_norm (1) +
              harvest_value_norm (1) + distance_to_next_threshold_norm (1)
  [22..29]  — hand type counts (8)
  [30]      — hand size normalized
  [31..38]  — drawn card type counts (8)
  [39..46]  — traded card type counts (8)
  [47]      — deck size normalized
  [48]      — round normalized
  [49]      — own coins normalized
  [50..52]  — opponent coins (up to 3, padded) normalized
  [53..56]  — phase one-hot (4)
  [57..72]  — opponent field summaries (up to 2 opponents × 2 fields × 2: type_idx_norm + count_norm)
  [73]      — is_last_round: 1.0 if round == 2 (final deck pass), else 0.0
  [74]      — deck_urgency: fraction of last-round cards already consumed (0 outside last round)
  Total = 75
"""
from __future__ import annotations

import numpy as np

from card_config import NUM_CARD_TYPES, TOTAL_CARDS, NAME_TO_INDEX, harvest_value, next_threshold

STATE_SIZE = 75

# Normalization constants
MAX_FIELD_SIZE = 20
MAX_COINS = 30
MAX_ROUNDS = 80
MAX_HAND = 20


def encode_state(env, player_idx: int) -> np.ndarray:
    """Encode game state from the perspective of ``player_idx``."""
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
    hand_counts = _type_counts(player.hand)
    vec[offset:offset + NUM_CARD_TYPES] = hand_counts / max(MAX_HAND, 1)
    offset += NUM_CARD_TYPES
    vec[offset] = min(len(player.hand) / MAX_HAND, 1.0)
    offset += 1

    # ── Drawn card type counts (8) ──────────────────────────────────
    drawn_counts = _type_counts(player.drawn_cards)
    vec[offset:offset + NUM_CARD_TYPES] = drawn_counts
    offset += NUM_CARD_TYPES

    # ── Traded card type counts (8) ─────────────────────────────────
    traded_counts = _type_counts(player.traded_cards)
    vec[offset:offset + NUM_CARD_TYPES] = traded_counts
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
    # Gives the agent an explicit signal that it should harvest before the game ends.
    # round == 2 means we are on the third (final) pass through the deck.
    is_last_round = 1.0 if env.round >= 2 else 0.0
    vec[offset] = is_last_round
    offset += 1
    if is_last_round:
        # how far through the last round are we: 0 = just started, 1 = almost empty
        one_round_cards = len(env.players) * 5  # 5 cards consumed per player turn
        vec[offset] = max(0.0, min(1.0, 1.0 - len(env.deck) / max(one_round_cards, 1)))
    offset += 1

    return vec


def _type_counts(cards) -> np.ndarray:
    """Count occurrences of each card type in a sequence of type-name strings."""
    counts = np.zeros(NUM_CARD_TYPES, dtype=np.float32)
    for name in cards:
        idx = NAME_TO_INDEX.get(name)
        if idx is not None:
            counts[idx] += 1.0
    return counts
