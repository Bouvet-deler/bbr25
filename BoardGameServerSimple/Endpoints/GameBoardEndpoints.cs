using BoardGameServer.Application;
namespace BoardGameServerSimple.Endpoints;

public static class GameBoardEndpoints
{
    public static IEndpointRouteBuilder MapGameBoardEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/game");

        group.MapGet("/", (Game game, Guid? playerKey) =>
        {
            var result = new
            {
                CurrentPlayer = game.CurrentPlayer == null ? "" : game.CurrentPlayer.Name,
                CurrentPhase = game.CurrentPhase,
                CurrentMode = game.CurrentState,
                Deck = game.Deck.Count(),
                AvailableTrades = game.TradingArea,
                DiscardPile = game.Discard,
                Players = game.Players
                ?.Select(p => new { 
                        p.Name,
                        p.Coins,
                        Fields = p.Fields,
                        Hand = p.Hand.Count(),
                        DrawnCards = p.DrawnCards,
                        TradedCards = p.TradedCards
                        })?.ToList(),
                YourHand = game.Players.Any() ?  game.Players.First(player => player.Id == playerKey)?.Hand : null ,
            };
            return TypedResults.Ok(result);
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Gets the state of the game";
            op.Description = "bruk din playerKey for å få se hånden din";
            return op;
        });

        group.MapPost("/join", (Game game, string name) =>
        {
            return TypedResults.Ok(game.Join(name));
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Join the game with a display name";
            op.Description = "";
            return op;
        });
        group.MapPost("/start", (Game game) =>
        {
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
}
