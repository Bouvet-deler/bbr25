"""
Bonanzha AI Agent Framework — core modules.

Provides the game simulator, API client, state encoder, and data objects
needed to build and train player agents.
"""
from .game_objects import (
    CardDto, HandCardDto, FieldDto, PlayerDto, TradeDto,
    GameStateDto, ExchangeMapEntry, OfferDto, Accept,
    dict_to_game_state,
)
from .card_config import (
    CARD_TYPES, NUM_CARD_TYPES, TOTAL_CARDS,
    NAME_TO_INDEX, INDEX_TO_NAME, NAME_TO_CARD_TYPE,
    harvest_value, next_threshold,
)
from .state_encoder import STATE_SIZE, encode_state, encode_live_state
from .api_client import GameApiClient
