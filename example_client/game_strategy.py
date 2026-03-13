"""
Game strategy / business logic.

All decision-making about planting, trading, and harvesting lives here.
This module uses GameApiClient to *execute* decisions but never constructs
URLs or handles HTTP directly.
"""
import logging
import random
from math import comb
from time import sleep

from game_objects import FieldDto, GameStateDto, HandCardDto, PlayerDto
from game_api_client import GameApiClient


class GameStrategy:
    """Encapsulates all game-play decision logic."""

    def __init__(self, api: GameApiClient) -> None:
        self.logger = logging.getLogger(f"Strategy.{api.game_name}")
        self.api = api

    # ── Helper ───────────────────────────────────────────────────────

    @staticmethod
    def can_harvest_field(player: PlayerDto, field) -> bool:
        """Check if a field can be harvested according to the bean-protection rule.

        Rule: Cannot harvest a field with 1 bean if ANY other field has 2+ beans.
        """
        field_size = len(field.card)

        if field_size >= 2:
            return True          # 2+ beans → always harvestable
        if field_size == 0:
            return False         # nothing to harvest

        # Field has exactly 1 bean – only allowed if no other field has 2+
        for other_field in player.fields:
            if other_field.key != field.key and len(other_field.card) >= 2:
                return False     # another field has 2+ beans → protected
        return True
    
    @staticmethod
    def harvest_value(field: FieldDto) -> int:
        """Calculate the coin payout for harvesting this field right now.

        Replicates the server's Harvest() logic: iterate the exchange_map
        (ordered largest crop_size first) and return the first matching value.
        """
        num_cards = len(field.card)
        if num_cards == 0:
            return 0
        for entry in field.card[0].exchange_map:
            if num_cards >= entry.crop_size:
                return entry.value
        return 0

    @staticmethod
    def estimate_total_of_type(
        card_type: str,
        cards_in_hand: list[HandCardDto],
        game_state: GameStateDto | None,
    ) -> int:
        """Estimate the total number of *card_type* cards that exist in the game.

        Used when the server does not populate ``total_number_of_type``.
        Counts every visible instance: on all players' fields, in our hand, and
        in the discard pile.  This is a lower bound on the true total, but it is
        far better than zero and keeps all downstream calculations meaningful.
        """
        count = sum(1 for c in cards_in_hand if c.type == card_type)
        if game_state is not None:
            for player in game_state.players:
                for field in player.fields:
                    count += sum(1 for c in field.card if c.type == card_type)
            count += sum(1 for c in game_state.discard_pile if c.type == card_type)
        return max(count, 1)  # at least 1 – we can always see the card we are evaluating

    @staticmethod
    def estimate_cards_in_deck(
        card_type: str,
        total_of_type: int,
        cards_in_hand: list[HandCardDto],
        game_state: GameStateDto,
    ) -> int:
        """Estimate how many cards of *card_type* are currently in the draw deck.

        Strategy: every card of this type that is visible (on any player's field,
        in our hand, or in the discard pile) is subtracted from *total_of_type*.
        The remaining *unobserved* cards are assumed uniformly distributed between
        the deck and the other players' hidden hands, so we scale by
        ``deck / (deck + other_hands)``.
        """
        if total_of_type <= 0:
            return 0

        visible = 0
        for player in game_state.players:
            for field in player.fields:
                visible += sum(1 for c in field.card if c.type == card_type)
        visible += sum(1 for c in cards_in_hand if c.type == card_type)
        visible += sum(1 for c in game_state.discard_pile if c.type == card_type)

        total_unobserved = max(0, total_of_type - visible)
        if total_unobserved == 0:
            return 0

        deck_size = game_state.deck
        # Other players' hidden hand sizes (our hand is already counted above)
        other_hands = max(0, sum(p.hand for p in game_state.players) - len(cards_in_hand))
        unobserved_pool = deck_size + other_hands

        if unobserved_pool <= 0:
            return 0

        return round(total_unobserved * deck_size / unobserved_pool)

    @staticmethod
    def prob_scoring_at_t(K: int, D: int, t: int, need: int) -> float:
        """Hypergeometric P(drawing >= *need* cards of one type in *t* draws).

        Parameters
        ----------
        K    : desired cards currently in the deck
        D    : total cards in the deck
        t    : number of draws (turns ahead)
        need : how many more of this type are required to reach the next threshold
        """
        if need <= 0:
            return 1.0
        if K <= 0 or D <= 0 or t < need:
            return 0.0
        t = min(t, D)
        total_ways = comb(D, t)
        if total_ways == 0:
            return 0.0

        prob_less = sum(
            comb(K, i) * comb(D - K, t - i)
            for i in range(need)
            if 0 <= t - i <= D - K
        )
        return 1.0 - prob_less / total_ways

    @staticmethod
    def weighted_future_scoring_prob(
        K_in_deck: int,
        deck_size: int,
        need: int,
        max_t: int = 5,
        gamma: float = 0.85,
    ) -> float:
        """Discount-weighted probability of scoring within the next *max_t* turns.

        Combines P(scoring at t+1), P(scoring by t+2), … using an exponential
        discount *gamma* so that nearer turns carry more weight.
        Returns a value in [0, 1].
        """
        if need <= 0:
            return 1.0
        weighted_sum = 0.0
        weight_total = 0.0
        for t in range(1, max_t + 1):
            weight = gamma ** t
            prob = GameStrategy.prob_scoring_at_t(K_in_deck, deck_size, t, need)
            weighted_sum += weight * prob
            weight_total += weight
        return weighted_sum / weight_total if weight_total > 0 else 0.0

    @staticmethod
    def field_to_harvest_algorithm(
        harvestable_fields: list[FieldDto],
        cards_in_hand: list[HandCardDto],
        game_state: GameStateDto | None = None,
    ) -> FieldDto:
        """Pick the field whose harvest costs the least (value + future potential).

        Decision priority (lowest cost = harvested first):
          1. Lowest current coin value
          2. Lowest weighted future-scoring probability (least hope for this field)
          3. Lowest simulated card count when hand cards are included
          4. Smallest fraction of that type already controlled
          5. Most common card type (easiest to rebuild)

        When *game_state* is provided the future-scoring probability is computed
        via a hypergeometric model over t+1 … t+5 turns with exponential discounting.
        Without it the method falls back to a simpler heuristic.
        """
        field_information_matrix = []

        for field in harvestable_fields:
            card_type       = field.card[0].type
            exchange_map    = field.card[0].exchange_map
            total_of_type   = field.card[0].total_number_of_type or GameStrategy.estimate_total_of_type(
                card_type, cards_in_hand, game_state
            )
            field_size      = len(field.card)

            # Current coin value if harvested right now
            current_value = max(
                (e.value for e in exchange_map if e.crop_size <= field_size),
                default=0,
            )

            # Cards of this type in hand
            hand_matches = sum(1 for c in cards_in_hand if c.type == card_type)
            simulated_count = field_size + hand_matches 

            # Fraction of this type we already "control"
            percentage_held = simulated_count / total_of_type if total_of_type > 0 else 0.0

            # Cards still needed to reach the NEXT scoring threshold
            next_threshold = next(
                (e.crop_size for e in exchange_map if e.crop_size > field_size),
                None,
            )

            # --- Future-scoring probability ---
            if next_threshold is None:
                # Already at (or past) the highest threshold – no further upside
                future_prob = 0.0
            elif game_state is not None and game_state.deck > 0:
                need = next_threshold - field_size
                K = GameStrategy.estimate_cards_in_deck(
                    card_type, total_of_type, cards_in_hand, game_state
                )
                future_prob = GameStrategy.weighted_future_scoring_prob(
                    K, game_state.deck, need
                )
            else:
                # Fallback: simple proportion of cards remaining
                need = next_threshold - field_size
                future_prob = (hand_matches / total_of_type) if total_of_type > 0 else 0.0

            field_information_matrix.append({
                "field":            field,
                "current_value":    current_value,
                "future_prob":      future_prob,
                "simulated_count":  simulated_count,
                "percentage_held":  percentage_held,
                "commonality":      total_of_type,
            })

        return min(
            field_information_matrix,
            key=lambda x: (
                x["current_value"],       # harvest lowest immediate coin value first
                x["future_prob"],         # harvest field with least future scoring hope
                x["simulated_count"],     # harvest field with least growth potential
                x["percentage_held"],     # harvest where we hold the smallest fraction
                -x["commonality"],        # harvest most common type (easiest to rebuild)
            ),
        )["field"]

    # ── Display helpers ──────────────────────────────────────────────

    @staticmethod
    def _fmt_hand(cards) -> str:
        """Format a card list as 'TypeA×3, TypeB, …' grouped by type."""
        if not cards:
            return "(empty)"
        from collections import Counter
        counts = Counter(c.type for c in cards)
        return ", ".join(f"{t}×{n}" if n > 1 else t for t, n in counts.items())

    @staticmethod
    def _fmt_fields(fields: list[FieldDto]) -> str:
        """Format fields as 'Field 1: TypeA×3  |  Field 2: empty'."""
        parts = []
        for i, f in enumerate(fields, 1):
            if f.card:
                parts.append(f"Field {i}: {f.card[0].type}×{len(f.card)}")
            else:
                parts.append(f"Field {i}: empty")
        return "  |  ".join(parts)

    def _harvest_for_space(
        self, player_id: str, player: PlayerDto, field: FieldDto, reason: str = ""
    ) -> None:
        """Harvest a field, print coins earned (or 0), then return."""
        coins = self.harvest_value(field)
        card_type = field.card[0].type if field.card else "unknown"
        count = len(field.card)
        self.api.harvest_field(player_id, field.key)
        suffix = f" — {reason}" if reason else ""
        if coins > 0:
            print(f"   💰 {player.name} harvested {count}×{card_type}"
                  f" → +{coins} coin{'s' if coins != 1 else ''}{suffix}")
        else:
            print(f"   🌾 {player.name} harvested {count}×{card_type} (0 coins){suffix}")

    # ── Planting ─────────────────────────────────────────────────────

    def planting_strategy(self, game_state: GameStateDto, current_player: PlayerDto, player_id: str) -> None:
        """Plant the first card in hand onto a suitable field."""
        cards_in_hand = self.api.get_game(player_id=player_id).your_hand

        if not cards_in_hand:
            self.api.end_planting(player_id)
            raise Exception("No cards to plant")

        print(f"  Hand ({len(cards_in_hand)}): {self._fmt_hand(cards_in_hand)}")
        print(f"  Fields: {self._fmt_fields(current_player.fields)}")

        potential_fields = [
            f for f in current_player.fields
            if len(f.card) == 0 or f.card[0].type == cards_in_hand[0].type
        ]

        if not potential_fields:
            # Need to harvest a field first
            harvestable_fields = [
                f for f in current_player.fields
                if self.can_harvest_field(current_player, f)
            ]
            if harvestable_fields:
                fresh_state_for_harvest = self.api.get_game(player_id=player_id)
                field_to_harvest = self.field_to_harvest_algorithm(
                    harvestable_fields, cards_in_hand, fresh_state_for_harvest
                )
                self._harvest_for_space(player_id, current_player, field_to_harvest, "to make room for planting")
                potential_fields = [field_to_harvest]
            else:
                print("   ⊗ Cannot harvest any field – all protected by bean protection rule")
                raise Exception("Cannot plant – all fields occupied and protected")

        field_to_plant = random.choice(potential_fields)
        response = self.api.plant(player_id, field_to_plant.key)

        if response != "plantet":
            print(f"  ✗ Failed to plant {cards_in_hand[0].type}: {response}")
            raise Exception(f"Failed to plant card: {response}")

        fresh_state = self.api.get_game(player_id=player_id)
        fresh_player = next(
            (p for p in fresh_state.players if p.name == current_player.name), current_player
        )
        idx = current_player.fields.index(field_to_plant)
        print(f"  → Planted {cards_in_hand[0].type} on Field {idx + 1}")
        print(f"  Fields after: {self._fmt_fields(fresh_player.fields)}")
        # Update current_player reference so subsequent phases see fresh fields
        current_player.fields = fresh_player.fields

    def optional_planting_strategy(self, game_state: GameStateDto, current_player: PlayerDto, player_id: str) -> None:
        """Optionally plant the second card only when it is clearly beneficial.

        Decision rules (in order):
        1. If the card matches an existing field → always plant (free extension of a row).
        2. If no field is reachable without harvesting → skip (never harvest for an optional plant).
        3. If only a free field is available → plant only when the card's weighted
           future-scoring probability exceeds OPTIONAL_PLANT_THRESHOLD; otherwise skip.
        """
        OPTIONAL_PLANT_THRESHOLD = 0.35

        fresh_state = self.api.get_game(player_id=player_id)
        cards_in_hand = fresh_state.your_hand
        if not cards_in_hand:
            self.api.end_planting(player_id)
            return

        fresh_player = next(
            (p for p in fresh_state.players if p.name == current_player.name), current_player
        )
        card = cards_in_hand[0]

        print(f"  Next card: {card.type}")
        print(f"  Fields: {self._fmt_fields(fresh_player.fields)}")

        matching_fields = [f for f in fresh_player.fields if f.card and f.card[0].type == card.type]
        free_fields     = [f for f in fresh_player.fields if len(f.card) == 0]

        if matching_fields:
            # Extending an existing row is always worthwhile
            field_to_plant = matching_fields[0]

        elif free_fields:
            # Opening a new row: only worth it if the card has decent future potential
            total_of_type = card.total_number_of_type or GameStrategy.estimate_total_of_type(
                card.type, cards_in_hand, fresh_state
            )
            next_threshold = next(
                (e.crop_size for e in card.exchange_map if e.crop_size > 1), None
            )
            if next_threshold is not None and fresh_state.deck > 0:
                need = next_threshold - 1  # one card would be on the field after planting
                K = GameStrategy.estimate_cards_in_deck(
                    card.type, total_of_type, cards_in_hand, fresh_state
                )
                future_prob = GameStrategy.weighted_future_scoring_prob(K, fresh_state.deck, need)
            else:
                future_prob = 0.0

            if future_prob >= OPTIONAL_PLANT_THRESHOLD:
                field_to_plant = free_fields[0]
                print(f"  → Will plant on new row (future_prob={future_prob:.2f} ≥ {OPTIONAL_PLANT_THRESHOLD})")
            else:
                print(f"  ↩ Skipping — future_prob={future_prob:.2f} < {OPTIONAL_PLANT_THRESHOLD} (not worth opening a new row)")
                self.api.end_planting(player_id)
                return

        else:
            # Every field is occupied with a different type – harvesting is not worth it
            print(f"  ↩ Skipping — no free slot without harvesting (not worth it for an optional plant)")
            self.api.end_planting(player_id)
            return

        response = self.api.plant(player_id, field_to_plant.key)
        if response != "plantet":
            print(f"  ✗ Failed optional plant of {card.type}: {response}")
        else:
            idx = fresh_player.fields.index(field_to_plant)
            print(f"  → Optional-planted {card.type} on Field {idx + 1}")
        # Propagate field changes so subsequent phases see the updated state
        updated = self.api.get_game(player_id=player_id)
        refreshed = next((p for p in updated.players if p.name == current_player.name), None)
        if refreshed:
            current_player.fields = refreshed.fields
        print(f"  Fields after: {self._fmt_fields(current_player.fields)}")

    # ── Trade-planting ───────────────────────────────────────────────

    @staticmethod
    def _field_placement_priority(card_type: str, fields: list[FieldDto]) -> int:
        """Priority for placing *card_type* given the player's current fields.

        0 – an existing field already holds this type (just extend it, no harvest)
        1 – a free field is available (open a new row, no harvest)
        2 – every field is occupied with a different type (harvest required)
        """
        if any(f.card and f.card[0].type == card_type for f in fields):
            return 0
        if any(len(f.card) == 0 for f in fields):
            return 1
        return 2

    def trade_planting_strategy(self, game_state: GameStateDto, current_player: PlayerDto, player_id: str) -> None:
        """Plant all traded / drawn cards that must be placed after the trade phase.

        Cards are processed in order of how easily they can be placed:
          1. Cards that extend an existing matching field (no harvest needed)
          2. Cards that fit into a free field   (no harvest needed)
          3. Cards that require harvesting a field first

        The order is re-evaluated after each placement so that newly freed or
        newly filled fields are taken into account.
        """
        remaining_cards = list(current_player.traded_cards)
        if current_player.name == game_state.current_player:
            remaining_cards += current_player.drawn_cards[:2]

        if not remaining_cards:
            print(f"  (no cards to plant)")
            return

        print(f"  Must plant: {self._fmt_hand(remaining_cards)}")

        while remaining_cards:
            # Refresh field data from server so we see the real state after previous operations
            fresh_state = self.api.get_game(player_id=player_id)
            fresh_player = next(
                (p for p in fresh_state.players if p.name == current_player.name), current_player
            )

            # Re-sort remaining cards: easiest-to-place first
            remaining_cards.sort(
                key=lambda c: self._field_placement_priority(c.type, fresh_player.fields)
            )
            card = remaining_cards.pop(0)

            field_with_same_card = [
                f for f in fresh_player.fields if f.card and f.card[0].type == card.type
            ]
            free_field = [f for f in fresh_player.fields if len(f.card) == 0]
            potential_fields = field_with_same_card if field_with_same_card else free_field

            if not potential_fields:
                # Need to harvest to make room
                harvestable_fields = [
                    f for f in fresh_player.fields
                    if self.can_harvest_field(fresh_player, f)
                ]
                if harvestable_fields:
                    field_to_harvest = self.field_to_harvest_algorithm(
                        harvestable_fields, fresh_state.your_hand, fresh_state
                    )
                    try:
                        self._harvest_for_space(player_id, fresh_player, field_to_harvest, "to make room for trade-plant")
                        potential_fields.append(field_to_harvest)
                    except Exception as e:
                        print(f"  ✗ Could not harvest field for {current_player.name}: {e}")

                if not potential_fields:
                    print(f"  ⊗ Skipping {card.type} – all fields occupied and protected by bean rule")
                    continue

            field_to_plant = random.choice(potential_fields)
            field_index = fresh_player.fields.index(field_to_plant)
            response = self.api.trade_plant(player_id, card.id, field_to_plant.key)
            if response != "Plantet etter byttene":
                print(f"  ✗ Failed to trade-plant {card.type}: {response}")
                raise Exception(f"Failed to trade-plant card: {response}")
            else:
                print(f"  → Trade-planted {card.type} on Field {field_index + 1}")

        # Print final field state after all trade-plants
        final_state = self.api.get_game(player_id=player_id)
        final_player = next((p for p in final_state.players if p.name == current_player.name), None)
        if final_player:
            print(f"  Fields after: {self._fmt_fields(final_player.fields)}")

    # ── Trading ──────────────────────────────────────────────────────

    def trading_strategy(self, game_state: GameStateDto, current_player: PlayerDto, player_id: str) -> None:
        """Post a trade offer for the active player.

        Offers ALL undesired cards (any number) in exchange for ALL desired types
        (any number), which is explicitly permitted by the rules.
        Priority for which cards to offer:
          1. Drawn cards that don't match any owned field (must be dealt with anyway)
          2. Hand cards that don't match any owned field
        Cards received in a previous trade (TradedCards) are excluded automatically
        because the server never includes them in your_hand.
        """
        turned_over_cards = list(current_player.drawn_cards)[:2]
        cards_in_hand = self.api.get_game(player_id=player_id).your_hand

        print(f"  Fields: {self._fmt_fields(current_player.fields)}")
        print(f"  Drawn:  {self._fmt_hand(turned_over_cards)}")
        print(f"  Hand ({len(cards_in_hand)}): {self._fmt_hand(cards_in_hand)}")

        owned_types = {f.card[0].type for f in current_player.fields if f.card}

        # Offer only drawn cards that don't match an owned field — these must be
        # planted in TradePlanting anyway, so trading them away is a free action.
        # Offering hand cards is almost always bad: the accepter receives every
        # offered card, so handing over many cards for one in return is a poor deal.
        undesired_drawn = [c for c in turned_over_cards if c.type not in owned_types]

        if undesired_drawn:
            cards_to_offer = undesired_drawn
        else:
            # Both drawn cards match owned fields (we want them) — offer the single
            # least-useful hand card as a token offer, but only if we have a clear
            # desired type to request in return.
            undesired_hand = [c for c in cards_in_hand if c.type not in owned_types]
            cards_to_offer = undesired_hand[:1]  # at most one hand card

        if not cards_to_offer or not owned_types:
            print(f"  → Nothing useful to offer or request, skipping trade")
            self.api.end_trading(player_id)
            return

        desired_types = list(owned_types)

        try:
            response = self.api.request_trade(
                player_id,
                [c.id for c in cards_to_offer],
                desired_types,
            )
            if response:
                offer_str   = ', '.join(c.type for c in cards_to_offer)
                desired_str = ', '.join(desired_types)
                print(f"  → Offering [{offer_str}] for any [{desired_str}]")
                sleep(5)  # Give other players time to evaluate and accept
        except Exception as e:
            self.logger.error(f"Error making trade offer: {e}", exc_info=True)

        self.api.end_trading(player_id)

    def optional_trading_strategy(self, game_state: GameStateDto, current_player: PlayerDto, player_id: str) -> None:
        """Evaluate outstanding trades and accept one if it is beneficial.

        Pays with ALL cards in hand that match what the initiator wants, which is
        legal (any number for any number). Cards already received in a trade are
        excluded automatically — they are in TradedCards, not your_hand.
        """
        posted_trades = game_state.available_trades
        if not posted_trades:
            return

        initiator_name = game_state.current_player
        owned_types = {f.card[0].type for f in current_player.fields if f.card}

        for trade in posted_trades:
            # Does the offer contain anything useful to us?
            wanted_from_offer = [t for t in trade.offered_cards if t in owned_types]
            if not wanted_from_offer:
                self.logger.debug(
                    f"{current_player.name} skips {initiator_name}'s trade – "
                    "offered cards don't match any field"
                )
                continue

            # Give the single card of the wanted type that we hold the most duplicates
            # of (least painful to part with). Giving more than one is almost never
            # strategically sound.
            matching_hand = [c for c in game_state.your_hand if c.type in trade.card_types_wanted]
            if not matching_hand:
                self.logger.debug(
                    f"{current_player.name} cannot accept {initiator_name}'s trade – "
                    "no matching cards in hand"
                )
                continue
            from collections import Counter
            type_counts = Counter(c.type for c in matching_hand)
            best_type   = max(type_counts, key=type_counts.get)
            cards_to_give = [next(c for c in matching_hand if c.type == best_type)]
            if not cards_to_give:
                self.logger.debug(
                    f"{current_player.name} cannot accept {initiator_name}'s trade – "
                    "no matching cards in hand"
                )
                continue

            try:
                response = self.api.accept_trade(
                    player_id,
                    trade.negotiation_id,
                    [c.id for c in cards_to_give],
                )
                received_str = ', '.join(wanted_from_offer)
                given_str    = ', '.join(c.type for c in cards_to_give)
                print(f"  🤝 {current_player.name} accepts {initiator_name}'s trade:")
                print(f"     ← receives [{received_str}] from {initiator_name}")
                print(f"     → gives    [{given_str}] to {initiator_name}")
                return
            except Exception as e:
                if "404" in str(e):
                    self.logger.debug(f"{current_player.name} tried to accept trade but it was already taken")
                else:
                    print(f"  ✗ Error accepting trade: {e}")
