using BoardGameServer.Application;
using BoardGameServer.Application.Services;
using SharedModels;
using Microsoft.AspNetCore.Mvc;
namespace BoardGameServerSimple.Endpoints;

public static class GameBoardEndpoints
{
    public static IEndpointRouteBuilder MapGameBoardEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/game");

        group.MapGet("/", ( string? player, [FromServices] GameService gameService) =>
        {
            Guid playerKey;
            var game = gameService.GetCurrentGame();
            Queue<Card> hand = new Queue<Card>(); ;
            if (Guid.TryParse(player, out playerKey))
            {
                var p = game.Players.FirstOrDefault(p => p.Id == playerKey);
                if (p != null) hand = p.Hand;
            }
            object result = CreateGameState(game, hand);
            return TypedResults.Ok(result);
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Gets the state of the game";
            op.Description = "bruk din playerKey for å få se hånden din";
            return op;
        });

        group.MapPost("/join", ( string name, [FromServices] GameService gameService) =>
        {
            var game = gameService.GetCurrentGame();
            return TypedResults.Ok(game.Join(name));
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Join the game with a display name";
            op.Description = "";
            return op;
        });

        group.MapPost("/start", ([FromServices] GameService gameService) =>
        {
            var game = gameService.GetCurrentGame();
            game.StartGame();
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Starts the game";
            op.Description = "Starts the game. This will destroy any game in progress.";
            return op;
        });

        group.MapPost("/stop", () =>
        {
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Stops the game";
            op.Description = "Stops the game and scores all players cards.";
            return op;
        });
        return routes;
    }
    static object CreateGameState(Game game, Queue<Card> hand)
    {
        return new
        {
            CurrentPlayer = game.CurrentPlayer == null ? "" : game.CurrentPlayer.Name,
            CurrentPhase = PhaseUtil.GetDescription(game.CurrentPhase),
            CurrentState = StateUtil.GetDescription(game.CurrentState),
            Deck = game.Deck.Count(),
            AvailableTrades = game.TradingArea,
            DiscardPile = game.Discard,
            Players = game.Players
            ?.Select(p => new
            {
                p.Name,
                p.Coins,
                Fields = p.Fields.Select(kv => new { kv.Key, Card = kv.Value.Select(c => new { c.Id, c.Type }) }),
                Hand = p.Hand.Count(),
                DrawnCards = p.DrawnCards.Select(c => new { c.Id, c.Type }),
                TradedCards = p.TradedCards.Select(c => new { c.Id, c.Type })
            })?.ToList(),
            YourHand = hand.Select(c => new
            {
                FirstCard = hand.Peek() == c, //Bare for å gjøre det ekstra tydlig hvilket kort de kan spille
                c.Id,
                c.Type
            })
        };
    }

}
