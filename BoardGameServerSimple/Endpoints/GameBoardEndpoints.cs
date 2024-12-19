using BoardGameServer.Application;
namespace BoardGameServerSimple.Endpoints;

public static class GameBoardEndpoints
{
    public static IEndpointRouteBuilder MapGameBoardEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/game");

        group.MapGet("/", () =>
        {
            /* var gameState = gameStateManager.GetGameState(); */
            /* var result = new */
            /* { */
            /*     gameState.DeckPlayed, */
            /*     CurrentPlayer = gameState.CurrentPlayer != null ? new { gameState.CurrentPlayer.Name, gameState.CurrentPlayer.Score } : null, */
            /*     Players = gameState.Players?.Select(p => new { p.Name, p.Score }).ToList(), */
            /*     Deck = gameState.Deck.Select(c => new { c.CardType, c.Beanometer, c.Quantity }).ToList(), */
            /*     DiscardPile = gameState.DiscardPile.Select(c => new { c.CardType, c.Beanometer, c.Quantity }).ToList(), */
            /*     NextPlayer = gameState.NextPlayer != null ? new { gameState.NextPlayer.Name, gameState.NextPlayer.Score } : null */
            /* }; */
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Gets the state of the game";
            op.Description = "More detailed description";
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
