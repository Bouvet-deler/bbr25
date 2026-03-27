"""
Game data objects mirroring the C# DTOs from the API.

These dataclasses represent the game state as returned by the server.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ExchangeMapEntry:
    """How many cards of a type must be harvested for a given coin payout."""
    crop_size: int
    value: int


@dataclass
class CardDto:
    """A card in the game (on a field, in drawn/traded cards, or discard pile)."""
    id: str
    type: str
    total_number_of_type: Optional[int] = None
    exchange_map: List[ExchangeMapEntry] = field(default_factory=list)


@dataclass
class HandCardDto:
    """A card in the player's hand (includes ordering info)."""
    first_card: bool
    id: str
    type: str
    total_number_of_type: int
    exchange_map: List[ExchangeMapEntry] = field(default_factory=list)


@dataclass
class FieldDto:
    """A planting field (each player has 2). Contains a list of cards of the same type."""
    key: str
    card: List[CardDto] = field(default_factory=list)


@dataclass
class PlayerDto:
    """A player's visible state."""
    name: str
    coins: int
    fields: List[FieldDto] = field(default_factory=list)
    hand: int = 0  # number of cards (hidden from other players)
    drawn_cards: List[CardDto] = field(default_factory=list)
    traded_cards: List[CardDto] = field(default_factory=list)
    is_active: bool = True


@dataclass
class TradeDto:
    """A trade offer posted during the Trading phase."""
    initiator_id: str
    negotiation_id: str
    offered_cards: List[str] = field(default_factory=list)
    card_types_wanted: List[str] = field(default_factory=list)


@dataclass
class GameStateDto:
    """Complete game state as returned by the server."""
    name: str
    current_player: str
    current_phase: str          # "Planting", "PlantingOptional", "Trading", "TradePlanting"
    current_state: str          # "Registering", "Playing", "GameDone"
    round: int
    phase_time_left: str
    phase_end_timestamp: str
    last_state_change: str
    deck: int
    available_trades: List[TradeDto] = field(default_factory=list)
    discard_pile: List[CardDto] = field(default_factory=list)
    players: List[PlayerDto] = field(default_factory=list)
    your_hand: List[HandCardDto] = field(default_factory=list)


@dataclass
class OfferDto:
    """Trade offer request body."""
    offered_cards: List[str] = field(default_factory=list)
    card_types_wanted: List[str] = field(default_factory=list)


@dataclass
class Accept:
    """Trade acceptance request body."""
    negotiation_id: str
    payment: List[str] = field(default_factory=list)


def dict_to_game_state(data: dict) -> GameStateDto:
    """Convert API response dictionary to GameStateDto."""
    if not isinstance(data, dict):
        return data

    trades = [
        TradeDto(
            initiator_id=t.get('initiatorId', ''),
            negotiation_id=t.get('negotiationId', ''),
            offered_cards=t.get('offeredCards', []),
            card_types_wanted=t.get('cardTypesWanted', [])
        )
        for t in data.get('availableTrades', [])
    ]

    players = [
        PlayerDto(
            name=p.get('name', ''),
            coins=p.get('coins', 0),
            fields=[
                FieldDto(
                    key=f.get('key', ''),
                    card=[
                        CardDto(
                            id=c.get('id', ''),
                            type=c.get('type', ''),
                            total_number_of_type=c.get('totalNumberOfType'),
                            exchange_map=[
                                ExchangeMapEntry(
                                    crop_size=em.get('cropSize', 0),
                                    value=em.get('value', 0)
                                )
                                for em in c.get('exchangeMap', [])
                            ]
                        )
                        for c in f.get('card', [])
                    ]
                )
                for f in p.get('fields', [])
            ],
            hand=p.get('hand', 0),
            drawn_cards=[
                CardDto(
                    id=c.get('id', ''),
                    type=c.get('type', ''),
                    total_number_of_type=c.get('totalNumberOfType'),
                    exchange_map=[
                        ExchangeMapEntry(
                            crop_size=em.get('cropSize', 0),
                            value=em.get('value', 0)
                        )
                        for em in c.get('exchangeMap', [])
                    ]
                )
                for c in p.get('drawnCards', [])
            ],
            traded_cards=[
                CardDto(
                    id=c.get('id', ''),
                    type=c.get('type', '')
                )
                for c in p.get('tradedCards', [])
            ],
            is_active=p.get('isActive', True)
        )
        for p in data.get('players', [])
    ]

    your_hand = [
        HandCardDto(
            first_card=h.get('firstCard', False),
            id=h.get('id', ''),
            type=h.get('type', ''),
            total_number_of_type=h.get('totalNumberOfType', 0),
            exchange_map=[
                ExchangeMapEntry(
                    crop_size=em.get('cropSize', 0),
                    value=em.get('value', 0)
                )
                for em in h.get('exchangeMap', [])
            ]
        )
        for h in data.get('yourHand', [])
    ]

    return GameStateDto(
        name=data.get('name', ''),
        current_player=data.get('currentPlayer', ''),
        current_phase=data.get('currentPhase', ''),
        current_state=data.get('currentState', ''),
        round=data.get('round', 0),
        phase_time_left=data.get('phaseTimeLeft', ''),
        phase_end_timestamp=data.get('phaseEndTimestamp', ''),
        last_state_change=data.get('lastStateChange', ''),
        deck=data.get('deck', 0),
        available_trades=trades,
        discard_pile=[],
        players=players,
        your_hand=your_hand
    )
