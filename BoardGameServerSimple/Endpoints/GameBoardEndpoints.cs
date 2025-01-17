using BoardGameServer.Application;
using BoardGameServer.Application.Services;
using SharedModels;
using Microsoft.AspNetCore.Mvc;
using BoardGameServer.Application.Models;
using Microsoft.AspNetCore.Http.HttpResults;
namespace BoardGameServerSimple.Endpoints;

public static class GameBoardEndpoints
{
    public static IEndpointRouteBuilder MapGameBoardEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/game");
        group.MapGet("/all", (string? playerId, [FromServices] GameService gameService) =>
        {
            Guid playerKey;
            var game = gameService.GetCurrentGame();
            Queue<Card> hand = new Queue<Card>();
            //Foreløpig gjøres dette bare her
            if (Guid.TryParse(playerId, out playerKey))
            {
                var p = game.Players.FirstOrDefault(p => p.Id == playerKey);
                if (p != null) hand = p.Hand;
            }
            var result = Game.CreateGameState(game, hand);
            var retur = new List<GameStateDto> { result, result, result, result, result };
            return TypedResults.Ok<List<GameStateDto>>(retur);
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Gets the state of the game";
            op.Description = "bruk din playerKey for å få se hånden din";
            return op;
        });
        group.MapGet("/", (string? playerId, [FromServices] GameService gameService) =>
        {
            Guid playerKey;
            var game = gameService.GetCurrentGame();
            Queue<Card> hand = new Queue<Card>(); ;
            //Foreløpig gjøres dette bare her
            if (Guid.TryParse(playerId, out playerKey))
            {
                var p = game.Players.FirstOrDefault(p => p.Id == playerKey);
                if (p != null) hand = p.Hand;
            }
            var result = Game.CreateGameState(game, hand);
            return TypedResults.Ok<GameStateDto>(result);
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Gets the state of the game";
            op.Description = "bruk din playerKey for å få se hånden din";
            return op;
        });

        group.MapGet("/join", static async Task<Results<Ok<Guid>, ValidationProblem>> (string name, Guid playerId, [FromServices] GameService gameService, ValidationRules validationRules) =>
        {
            var game = gameService.GetCurrentGame();
            game.Lock.Enter();

            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            validationRules.NotAlreadyJoined(game, name, errors);
            if (errors.Any())
            {
                game.Lock.Exit();
                return TypedResults.ValidationProblem(errors);
            }
            game.Lock.Exit();
            game.Join(name, playerId.ToString());
            return TypedResults.Ok(playerId);
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Join the game with a display name";
            op.Description = "";
            return op;
        });

        group.MapGet("/start", static async Task<Results<Ok, ValidationProblem>> (string key, [FromServices] GameService gameService, ValidationRules validationRules) =>
        {
            if (key != "BlåFjell2025")
            {
                return TypedResults.ValidationProblem(new Dictionary<string, string[]> { { "Error", new[] { "Not permitted" } } });
            }

            var game = gameService.GetCurrentGame();
            game.Lock.Enter();

            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            validationRules.NotAlreadyStarted(game, errors);
            if (errors.Any())
            {
                game.Lock.Exit();
                return TypedResults.ValidationProblem(errors);
            }
            game.StartGame();
            game.Lock.Exit();
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Starts the game";
            op.Description = "Starts the game. This will destroy any game in progress.";
            return op;
        });

        group.MapGet("/check-for-timeout", static async Task<Results<Ok, ValidationProblem>> ([FromServices] GameService gameService, ValidationRules validationRules) =>
        {
            var game = gameService.GetCurrentGame();
            game.Lock.Enter();
            game.CheckForTimeout();
            game.Lock.Exit();
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Starts the game";
            op.Description = "Starts the game. This will destroy any game in progress.";
            return op;
        });
        group.MapGet("/stop", () =>
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
