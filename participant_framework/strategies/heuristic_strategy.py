"""
Heuristic strategy — a solid rule-based baseline.

Uses hand-crafted rules for each game phase. No machine learning involved.
This is a good reference for what "reasonable play" looks like.

Expected performance: ~5-8 coins per game.

This strategy extends BaseStrategy directly (not ActionStrategy) because
rule-based logic benefits from full control over each phase.
"""
from time import sleep

from framework.game_objects import FieldDto, GameStateDto, HandCardDto, PlayerDto
from strategies.base_strategy import BaseStrategy


class HeuristicStrategy(BaseStrategy):
    """Rule-based strategy with hand-crafted game logic."""

    def planting_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        cards_in_hand = self.api.get_game(player_id=player_id).your_hand
        if not cards_in_hand:
            self.api.end_planting(player_id)
            return

        print(f"  Hand ({len(cards_in_hand)}): {self.fmt_hand(cards_in_hand)}")
        print(f"  Fields: {self.fmt_fields(current_player.fields)}")

        card = cards_in_hand[0]

        # Try matching field first, then empty field
        potential_fields = [
            f for f in current_player.fields
            if len(f.card) == 0 or f.card[0].type == card.type
        ]

        if not potential_fields:
            # Must harvest to make room — pick the least valuable field
            harvestable = [
                f for f in current_player.fields
                if self.can_harvest_field(current_player, f)
            ]
            if harvestable:
                field_to_harvest = min(harvestable, key=lambda f: self.harvest_value(f))
                coins = self.harvest_value(field_to_harvest)
                self.api.harvest_field(player_id, field_to_harvest.key)
                print(f"  → Harvested {len(field_to_harvest.card)}×{field_to_harvest.card[0].type} ({coins} coins)")
                potential_fields = [field_to_harvest]

        if not potential_fields:
            raise Exception("Cannot plant — all fields occupied and protected")

        # Prefer matching over empty field
        matching = [f for f in potential_fields if f.card and f.card[0].type == card.type]
        field_to_plant = matching[0] if matching else potential_fields[0]

        self.api.plant(player_id, field_to_plant.key)
        idx = current_player.fields.index(field_to_plant) + 1
        print(f"  → Planted {card.type} on Field {idx}")

        fresh = self.api.get_game(player_id=player_id)
        refreshed = next((p for p in fresh.players if p.name == current_player.name), None)
        if refreshed:
            current_player.fields = refreshed.fields
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
        card = cards_in_hand[0]

        # Only plant if the card matches an existing field (extending a row is free value)
        matching = [f for f in fresh_player.fields if f.card and f.card[0].type == card.type]
        if matching:
            self.api.plant(player_id, matching[0].key)
            idx = fresh_player.fields.index(matching[0]) + 1
            print(f"  → Optional-planted {card.type} on Field {idx}")
        else:
            # Don't open a new row or harvest just for an optional plant
            print(f"  → Skipping optional plant ({card.type} doesn't match any field)")
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
        turned_over = list(current_player.drawn_cards)[:2]
        print(f"  Fields: {self.fmt_fields(current_player.fields)}")
        print(f"  Drawn:  {self.fmt_hand(turned_over)}")

        # TODO: Decide which drawn cards (if any) to offer in a trade.
        #
        # Things to consider:
        #   - Which drawn cards match your existing fields? Keep those — they're free value.
        #   - Which drawn cards are undesired? Offer those to others.
        #   - What card types would you want in return?
        #   - Is it worth adding a hand card to sweeten the deal?
        #
        # Useful API calls:
        #   self.api.request_trade(player_id, offer_card_ids, wanted_card_types)
        #   self.api.end_trading(player_id)
        #
        # Available data:
        #   turned_over           — the two drawn cards (list of CardDto)
        #   current_player.fields — your current fields
        #   self.api.get_game(player_id=player_id).your_hand — your full hand

        # For now, keep both drawn cards and skip trading:
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

        # Sort: cards matching existing fields first (cheapest to place)
        def placement_priority(card):
            for f in current_player.fields:
                if f.card and f.card[0].type == card.type:
                    return 0  # matches existing field
            for f in current_player.fields:
                if not f.card:
                    return 1  # empty field available
            return 2  # must harvest

        remaining.sort(key=placement_priority)

        for card in remaining:
            fresh = self.api.get_game(player_id=player_id)
            fresh_p = next(
                (p for p in fresh.players if p.name == current_player.name), current_player
            )

            matching = [f for f in fresh_p.fields if f.card and f.card[0].type == card.type]
            empty = [f for f in fresh_p.fields if not f.card]
            target_fields = matching or empty

            if not target_fields:
                harvestable = [f for f in fresh_p.fields if self.can_harvest_field(fresh_p, f)]
                if harvestable:
                    to_harvest = min(harvestable, key=lambda f: self.harvest_value(f))
                    self.api.harvest_field(player_id, to_harvest.key)
                    print(f"  → Harvested to make room")
                    target_fields = [to_harvest]

            if not target_fields:
                print(f"  ⊗ Cannot place {card.type}")
                continue

            field = target_fields[0]
            fi = fresh_p.fields.index(field) + 1
            self.api.trade_plant(player_id, card.id, field.key)
            print(f"  → Trade-planted {card.type} on Field {fi}")

        final = self.api.get_game(player_id=player_id)
        final_p = next((p for p in final.players if p.name == current_player.name), None)
        if final_p:
            print(f"  Fields after: {self.fmt_fields(final_p.fields)}")

    def optional_trading_strategy(
        self, game_state: GameStateDto, current_player: PlayerDto, player_id: str
    ) -> None:
        # TODO: Decide whether to accept any of the available trade offers.
        # This is called during OTHER players' turns when trades are posted.
        #
        # Things to consider:
        #   - Does the offered card match one of your fields? Then it's worth taking.
        #   - Can you spare the card they're asking for?
        #   - Is the timing good — will you be able to plant the received card?
        #
        # Useful API calls:
        #   self.api.accept_trade(player_id, trade.negotiation_id, [card_id_to_give])
        #
        # Available data:
        #   game_state.available_trades  — list of open TradeDto offers
        #     trade.offered_cards        — card types being offered
        #     trade.card_types_wanted    — what the offerer wants in return
        #     trade.negotiation_id       — ID needed to accept
        #   current_player.fields        — your current fields
        #   game_state.your_hand         — cards in your hand

        # For now, accept nothing:
        pass
