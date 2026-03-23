"""
Card type configuration mirroring the server's Card.cs definitions.

Each card type has:
  - name: display name used by the server
  - count: total number in the 104-card deck
  - exchange_map: list of (crop_size, coin_value) sorted descending by crop_size
"""
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class CardType:
    name: str
    count: int
    exchange_map: Tuple[Tuple[int, int], ...]  # ((crop_size, value), ...) descending


# Matches the C# Card factory methods exactly
CARD_TYPES: Tuple[CardType, ...] = (
    CardType("Uranuceps",     8,  ((5, 4), (4, 3), (3, 2), (2, 1))),      # RedBean
    CardType("Merkubello",    6,  ((3, 3), (2, 2))),                       # GardenBean
    CardType("Marshwaganda", 10,  ((6, 4), (5, 3), (4, 2), (2, 1))),      # BlackEyedBean
    CardType("Saturnjong",   12,  ((7, 4), (6, 3), (4, 2), (2, 1))),      # SoyBean
    CardType("Jordflue",     14,  ((7, 4), (6, 3), (5, 2), (3, 1))),      # GreenBean
    CardType("Jupitail",     16,  ((8, 4), (7, 3), (5, 2), (3, 1))),      # StinkBean
    CardType("Plutos Mane",  18,  ((9, 4), (8, 3), (6, 2), (3, 1))),      # ChiliBean
    CardType("Venusvamp",    20,  ((10, 4), (8, 3), (6, 2), (4, 1))),     # BlueBean
)

NUM_CARD_TYPES = len(CARD_TYPES)
TOTAL_CARDS = sum(ct.count for ct in CARD_TYPES)  # 104

# Fast lookups
NAME_TO_INDEX = {ct.name: i for i, ct in enumerate(CARD_TYPES)}
INDEX_TO_NAME = {i: ct.name for i, ct in enumerate(CARD_TYPES)}
NAME_TO_CARD_TYPE = {ct.name: ct for ct in CARD_TYPES}


def harvest_value(card_type_name: str, num_cards: int) -> int:
    """Return coins earned from harvesting num_cards of the given type."""
    ct = NAME_TO_CARD_TYPE.get(card_type_name)
    if ct is None or num_cards == 0:
        return 0
    for crop_size, value in ct.exchange_map:
        if num_cards >= crop_size:
            return value
    return 0


def next_threshold(card_type_name: str, current_count: int) -> int | None:
    """Return the next crop_size threshold above current_count, or None."""
    ct = NAME_TO_CARD_TYPE.get(card_type_name)
    if ct is None:
        return None
    # exchange_map is descending; we want the smallest crop_size > current_count
    thresholds = sorted(cs for cs, _ in ct.exchange_map)
    for t in thresholds:
        if t > current_count:
            return t
    return None
