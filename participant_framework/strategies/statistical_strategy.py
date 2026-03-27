"""
Statistical / Bayesian strategy template.

Uses card counting and probability calculations to make decisions.
No training required — it works purely from visible information and
mathematical inference about unseen cards.

This template is a SKELETON — search for TODO to find the parts you
need to implement.

Playing: Run `python main.py --strategy statistical`

Key concepts:
  - Count all visible cards (fields, discard, your hand) to infer
    what's in the deck
  - Use hypergeometric distribution to calculate probability of drawing
    needed cards in the next N turns
  - Score each possible action by expected coin value
  - Make harvest/hold decisions based on probability of reaching the
    next threshold

Trade-offs vs ML approaches:
  + No training required — works immediately
  + Decisions are explainable and debuggable
  + Mathematically grounded
  + No model files to manage
  - Requires domain expertise to implement well
  - Doesn't adapt to opponent strategies
  - Complex probability calculations can be slow
  - Hard to handle trading decisions probabilistically
"""
from __future__ import annotations

from collections import Counter
from math import comb
from time import sleep
from typing import List, Optional

from framework.game_objects import FieldDto, GameStateDto, HandCardDto, PlayerDto
from framework.card_config import NAME_TO_CARD_TYPE, CARD_TYPES
from strategies.base_strategy import BaseStrategy


class StatisticalStrategy(BaseStrategy):
    """Probability-based strategy using card counting and expected value."""

    # ── Card Counting ────────────────────────────────────────────────

    @staticmethod
    def count_visible_cards(
        game_state: GameStateDto,
        hand_cards: list[HandCardDto],
    ) -> Counter:
        """Count all cards visible to us.

        TODO: Implement comprehensive card counting! Count cards in:
          - Your hand
          - All players' fields (visible to everyone)
          - Your drawn and traded cards
          - The discard pile
          - Other players' drawn/traded cards (visible during trade phase)

        Returns a Counter mapping card_type_name → count.
        """
        visible = Counter()

        # Count your hand
        for c in hand_cards:
            visible[c.type] += 1

        # TODO: Count cards on all players' fields
        for player in game_state.players:
            for field in player.fields:
                for card in field.card:
                    visible[card.type] += 1

        # TODO: Count drawn cards (visible during trading)
        for player in game_state.players:
            for card in player.drawn_cards:
                visible[card.type] += 1
            for card in player.traded_cards:
                visible[card.type] += 1

        # TODO: Count discard pile
        for card in game_state.discard_pile:
            visible[card.type] += 1

        return visible

    @staticmethod
    def estimate_cards_in_deck(
        card_type: str,
        visible_counts: Counter,
        game_state: GameStateDto,
    ) -> int:
        """Estimate how many cards of a type are in the draw deck.

        Total in game - visible = unobserved.
        Unobserved cards are split between deck and other players' hidden hands.
        Scale by deck/(deck + hidden_hands).

        TODO: Refine this estimate! Consider:
          - Track cards that have been discarded and reshuffled
          - Account for the fact that reshuffled discard → deck changes composition
          - Weight by probability based on opponent behavior
        """
        ct = NAME_TO_CARD_TYPE.get(card_type)
        if ct is None:
            return 0

        total_of_type = ct.count
        visible_of_type = visible_counts.get(card_type, 0)
        unobserved = max(0, total_of_type - visible_of_type)

        if unobserved == 0:
            return 0

        deck_size = game_state.deck
        # Other players' hidden hand sizes
        other_hands = sum(p.hand for p in game_state.players)
        unobserved_pool = deck_size + other_hands

        if unobserved_pool <= 0:
            return 0

        return round(unobserved * deck_size / unobserved_pool)

    @staticmethod
    def prob_drawing_needed(
        cards_in_deck: int,
        deck_size: int,
        draws: int,
        need: int,
    ) -> float:
        """P(drawing >= need cards of a type in the next draws).

        Uses the hypergeometric distribution:
          K = cards of desired type in deck
          N = total deck size
          n = number of draws
          k = number needed

        TODO: Consider extending this to account for:
          - Multiple turns of draws (not just immediate)
          - The fact that other players also draw cards
          - Deck reshuffles that change the composition
        """
        K, N, n = cards_in_deck, deck_size, draws
        if need <= 0:
            return 1.0
        if K <= 0 or N <= 0 or n < need:
            return 0.0
        n = min(n, N)
        total_ways = comb(N, n)
        if total_ways == 0:
            return 0.0

        # P(X < need) = sum of P(X = i) for i = 0 to need-1
        prob_less = sum(
            comb(K, i) * comb(N - K, n - i)
            for i in range(need)
            if 0 <= n - i <= N - K
        )
        return 1.0 - prob_less / total_ways

    def score_field_hold_value(
        self,
        field: FieldDto,
        hand_cards: list[HandCardDto],
        game_state: GameStateDto,
    ) -> float:
        """Score how valuable it is to KEEP a field (not harvest it).

        TODO: Implement a scoring function that considers:
          - Current harvest value (what you'd get now)
          - Probability of reaching the next threshold
          - How many turns are left (deck size / cards per turn)
          - How many cards of this type you have in hand
          - Risk of being forced to harvest before reaching threshold

        Returns a float where higher = more valuable to keep.
        """
        if not field.card:
            return 0.0

        card_type = field.card[0].type
        current_count = len(field.card)
        current_value = self.harvest_value(field)

        ct = NAME_TO_CARD_TYPE.get(card_type)
        if ct is None:
            return float(current_value)

        # Find next threshold
        thresholds = sorted(cs for cs, _ in ct.exchange_map)
        next_thresh = None
        for t in thresholds:
            if t > current_count:
                next_thresh = t
                break

        if next_thresh is None:
            # Already at max — harvest value is all we can get
            return float(current_value)

        need = next_thresh - current_count

        # How many of this type might be in the deck?
        visible = self.count_visible_cards(game_state, hand_cards)
        in_deck = self.estimate_cards_in_deck(card_type, visible, game_state)

        # Cards in hand that match
        hand_matches = sum(1 for c in hand_cards if c.type == card_type)

        # Probability of getting enough cards in the next 5 draws
        prob = self.prob_drawing_needed(in_deck, game_state.deck, 5, need - hand_matches)

        # Next threshold value
        next_value = 0
        for cs, v in ct.exchange_map:
            if cs == next_thresh:
                next_value = v
                break

        # TODO: Improve this formula! Consider:
        #   - Discount future value by turns remaining
        #   - Account for risk of losing the field
        #   - Factor in opportunity cost of holds field slot
        expected_future = prob * next_value
        return max(current_value, expected_future)

    # ── Phase Implementations ────────────────────────────────────────

    def planting_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        """Plant the first card, harvesting the least valuable field if needed.

        TODO: Use probability analysis to decide WHICH field to harvest:
          - Compare score_field_hold_value() for each field
          - Harvest the field with lower hold value
          - Consider if the card you're planting starts a valuable set
        """
        cards_in_hand = self.api.get_game(player_id=player_id).your_hand
        if not cards_in_hand:
            self.api.end_planting(player_id)
            return

        print(f"  Hand ({len(cards_in_hand)}): {self.fmt_hand(cards_in_hand)}")
        print(f"  Fields: {self.fmt_fields(current_player.fields)}")

        card = cards_in_hand[0]

        # Find valid fields (matching type or empty)
        matching = [f for f in current_player.fields if f.card and f.card[0].type == card.type]
        empty = [f for f in current_player.fields if not f.card]
        valid = matching if matching else empty

        if not valid:
            # Must harvest — use hold value to pick which
            harvestable = [f for f in current_player.fields if self.can_harvest_field(current_player, f)]
            if harvestable:
                # Harvest the field with LOWEST hold value
                to_harvest = min(
                    harvestable,
                    key=lambda f: self.score_field_hold_value(f, cards_in_hand, game_state)
                )
                self.api.harvest_field(player_id, to_harvest.key)
                coins = self.harvest_value(to_harvest)
                print(f"   → Harvested {len(to_harvest.card)}×{to_harvest.card[0].type} → {coins} coins")
                valid = [to_harvest]
            else:
                raise Exception("Cannot plant — all fields protected")

        field = matching[0] if matching else valid[0]
        self.api.plant(player_id, field.key)
        fi = current_player.fields.index(field)
        print(f"  → Planted {card.type} on Field {fi + 1}")

        fresh = self.api.get_game(player_id=player_id)
        fresh_p = next((p for p in fresh.players if p.name == current_player.name), current_player)
        current_player.fields = fresh_p.fields
        print(f"  Fields after: {self.fmt_fields(current_player.fields)}")

    def optional_planting_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        """Decide whether to plant the second card using probability analysis.

        TODO: Use card counting to decide:
          - If card matches existing field → probably yes (extends a row)
          - If card would go on empty field → calculate probability of
            reaching the first scoring threshold
          - If probability is high enough → plant; otherwise skip
        """
        fresh_state = self.api.get_game(player_id=player_id)
        cards_in_hand = fresh_state.your_hand
        if not cards_in_hand:
            self.api.end_planting(player_id)
            return

        fresh_player = next(
            (p for p in fresh_state.players if p.name == current_player.name), current_player
        )
        card = cards_in_hand[0]

        matching = [f for f in fresh_player.fields if f.card and f.card[0].type == card.type]
        if matching:
            self.api.plant(player_id, matching[0].key)
            print(f"  → Optional-planted {card.type} (extends row)")
        else:
            # TODO: Calculate if starting a new field is worth it
            # Consider: P(reaching threshold) × threshold_value vs opportunity cost
            print(f"  → Skipping optional plant")
            self.api.end_planting(player_id)
            return

        updated = self.api.get_game(player_id=player_id)
        refreshed = next((p for p in updated.players if p.name == current_player.name), None)
        if refreshed:
            current_player.fields = refreshed.fields
        print(f"  Fields after: {self.fmt_fields(current_player.fields)}")

    def trading_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        """Post trade offers based on expected value calculations.

        TODO: Use probability to evaluate trades:
          - Calculate expected value of keeping each drawn card
          - Compare with expected value of trading it for a desired type
          - Only offer cards whose keep-value is lower than trade-value
        """
        turned_over = list(current_player.drawn_cards)[:2]
        cards_in_hand = self.api.get_game(player_id=player_id).your_hand

        print(f"  Fields: {self.fmt_fields(current_player.fields)}")
        print(f"  Drawn:  {self.fmt_hand(turned_over)}")

        owned_types = {f.card[0].type for f in current_player.fields if f.card}
        undesired = [c for c in turned_over if c.type not in owned_types]

        if undesired and owned_types:
            try:
                self.api.request_trade(
                    player_id, [c.id for c in undesired], list(owned_types)
                )
                print(f"  → Offering {[c.type for c in undesired]} for {list(owned_types)}")
                sleep(5)
            except Exception as e:
                self.logger.error(f"Trade error: {e}")

        self.api.end_trading(player_id)

    def trade_planting_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        """Plant traded/drawn cards using hold-value analysis.

        TODO: When forced to harvest for room, use score_field_hold_value()
        to pick the least valuable field.
        """
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

            matching = [f for f in fresh_p.fields if f.card and f.card[0].type == card.type]
            free = [f for f in fresh_p.fields if not f.card]
            potential = matching if matching else free

            if not potential:
                harvestable = [f for f in fresh_p.fields if self.can_harvest_field(fresh_p, f)]
                if harvestable:
                    to_harvest = min(
                        harvestable,
                        key=lambda f: self.score_field_hold_value(
                            f, fresh.your_hand or [], fresh
                        )
                    )
                    self.api.harvest_field(player_id, to_harvest.key)
                    potential = [to_harvest]
                else:
                    print(f"  ⊗ Cannot plant {card.type}")
                    continue

            field = potential[0]
            self.api.trade_plant(player_id, card.id, field.key)
            fi = fresh_p.fields.index(field)
            print(f"  → Trade-planted {card.type} on Field {fi + 1}")

        final = self.api.get_game(player_id=player_id)
        final_p = next((p for p in final.players if p.name == current_player.name), None)
        if final_p:
            print(f"  Fields after: {self.fmt_fields(final_p.fields)}")

    def optional_trading_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        """Accept trades using expected value comparison.

        TODO: Calculate whether accepting is worth it:
          - EV(card received) = P(reaching threshold with it) × coin payout
          - EV(card given away) = loss to your own field plans
          - Accept if EV(received) > EV(given)
        """
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

            type_counts = Counter(c.type for c in matching)
            best_type = max(type_counts, key=type_counts.get)
            card_to_give = next(c for c in matching if c.type == best_type)

            try:
                self.api.accept_trade(player_id, trade.negotiation_id, [card_to_give.id])
                print(f"  🤝 Accepted: gave {card_to_give.type}, receiving {wanted}")
                return
            except Exception as e:
                if "404" not in str(e):
                    self.logger.error(f"Trade accept error: {e}")
