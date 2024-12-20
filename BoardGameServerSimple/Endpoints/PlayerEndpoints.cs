using BoardGameServerSimple.Services;
using BoardGameServer.Application;
using Microsoft.AspNetCore.Http.HttpResults;

namespace BoardGameServerSimple.Endpoints;

public static class PlayerEndpoints
{
    public static IEndpointRouteBuilder MapPlayerEndpoints(this IEndpointRouteBuilder routes)
    {

        var group = routes.MapGroup("/api/player");

        group.MapPost("/end-planting", static async Task<Results<Ok<string>, BadRequest>> (Game game, CardValidator cardValidator, string playerKey) =>
        {
            game.EndPlanting();
            /* if (cardValidator.Validate(card)) */
            /* { */
            /*     await gameStateManager.PlayCard(card); */
            /*     return TypedResults.Ok(card); */
            /* } */
            return TypedResults.BadRequest();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });
        group.MapPost("/plant", static async Task<Results<Ok, BadRequest>> (Game game, CardValidator cardValidator, string player, Guid field) =>
        {
            Guid playerKey;
            game.Plant(field);
            if (!Guid.TryParse(player, out playerKey)){}
            /* if (cardValidator.Validate(card)) */
            /* { */
            /*     await gameStateManager.PlayCard(card); */
            /*     return TypedResults.Ok(card); */
            /* } */
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapPost("/harvest-field", static async Task<Results<Ok, BadRequest>> (Game game, CardValidator cardValidator, string player, Guid field) =>
        {
Guid playerKey;
            if (!Guid.TryParse(player, out playerKey)){}
                Player p = game.Players.Where(c=>c.Id == playerKey).First();
            game.HarvestField(p, field);
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapPost("/end-trading", static async Task<Results<Ok, BadRequest>> (Game game, CardValidator cardValidator, string player, Guid bull) =>
        {
            Guid playerKey;
            if (!Guid.TryParse(player, out playerKey)){}
            game.EndTrading();
            /* if (cardValidator.Validate(card)) */
            /* { */
            /*     await gameStateManager.PlayCard(card); */
            /*     return TypedResults.Ok(card); */
            /* } */
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Ends the trading phase";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });
        group.MapPost("/plant-trade", static async Task<Results<Ok, BadRequest>> (Game game, CardValidator cardValidator, Guid playerKey, Guid cardId, Guid field) =>
        {
            //Følgene to linjer burde jo egentlig vært valideringskode.
            Player player = game.Players.Where(p=> p.Id == playerKey).First();
            Card card = player.DrawnCards.Where(c=> c.Id == cardId).Union(player.TradedCards.Where(c=>c.Id == cardId)).Single();
            game.PlantTrade(player, card, field);
            /* if (cardValidator.Validate(card)) */
            /* { */
            /*     await gameStateManager.PlayCard(card); */
            /*     return TypedResults.Ok(card); */
            /* } */
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Ends the trading phase";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });
        group.MapPost("/offer-trade", static async Task<Results<Ok, BadRequest>> (Game game, CardValidator cardValidator, Guid playerKey, Guid[] offeredCards) =>
        {

        //Denne må opp i parameterene men det er noe jeg ikke skjønner
        List<string> wantedRecieved  = null;
            Player player = game.Players.Where(p=> p.Id == playerKey).First();
            List<Card> cards = 
                player.DrawnCards.Where(c=> offeredCards.Contains(c.Id))
                .Union(player.TradedCards.Where(c=> offeredCards.Contains(c.Id))).ToList();
            Offer offer = new Offer(cards, wantedRecieved);
            game.OfferTrade(offer);
            /* if (cardValidator.Validate(card)) */
            /* { */
            /*     await gameStateManager.PlayCard(card); */
            /*     return TypedResults.Ok(card); */
            /* } */
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Ends the trading phase";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });
        group.MapPost("/accept-trade", static async Task<Results<Ok, BadRequest>> (Game game, CardValidator cardValidator, Guid playerKey, Guid offer, List<Guid> payment) =>
        {
            Player player = game.Players.Where(p=> p.Id == playerKey).First();
            game.AcceptTrade(player, offer, payment);
            /* if (cardValidator.Validate(card)) */
            /* { */
            /*     await gameStateManager.PlayCard(card); */
            /*     return TypedResults.Ok(card); */
            /* } */
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Ends the trading phase";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        return routes;
    }
}
