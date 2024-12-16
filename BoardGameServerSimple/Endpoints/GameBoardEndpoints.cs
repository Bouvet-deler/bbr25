using BoardGameServerSimple.Models;
using BoardGameServerSimple.Services;

namespace BoardGameServerSimple.Endpoints;

public static class GameBoardEndpoints
{
    public static IEndpointRouteBuilder MapGameBoardEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/game").WithTags(nameof(GameState));

        group.MapGet("/", (GameStateManager gameStateManager) =>
        {
            return TypedResults.Ok(gameStateManager.GetGameState());
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Gets the state of the game";
            op.Description = "More detailed description";
            return op;
        });

        group.MapPost("/start", (GameStateManager gameStateManager) =>
        {
            gameStateManager.StartGame();
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Starts the game";
            op.Description = "Starts the game. This will destroy any game in progress.";
            return op;
        });

        group.MapPost("/stop", (GameStateManager gameStateManager) =>
        {
            gameStateManager.StartGame();
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
