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
            var games = gameService.GetAllGames();
            Queue<Card> hand = new Queue<Card>(); ;
            
            List<GameStateDto> retur = new List<GameStateDto>{};
            foreach (var game in games)
            {
                try{
                    var result = Game.CreateGameState(game, hand);
                    if (Guid.TryParse(playerId, out playerKey)) {
                        var p = game.Players.FirstOrDefault(p => p.Id == playerKey);
                        if (p != null) hand = p.Hand;
                    }
                    retur.Add(Game.CreateGameState(game, hand));
                }
                finally{
                }
            }
            return TypedResults.Ok<List<GameStateDto>>(retur);
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Gets the state of the game";
            op.Description = "bruk din playerKey for å få se hånden din";
            return op;
        });
        group.MapGet("/", (string gameName, string? playerId, [FromServices] GameService gameService) =>
        {
            Guid playerKey;
            var game = gameService.GetGameByName(gameName);
            GameStateDto result;
            try{
            Queue<Card> hand = new Queue<Card>(); ;
            //Foreløpig gjøres dette bare her
            if (Guid.TryParse(playerId, out playerKey))
            {
                var p = game.Players.FirstOrDefault(p => p.Id == playerKey);
                if (p != null) hand = p.Hand;
            }
            result = Game.CreateGameState(game, hand);
            }finally{
                }
                return TypedResults.Ok<GameStateDto>(result);
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Gets the state of the game";
            op.Description = "bruk din playerKey for å få se hånden din";
            return op;
        });

        group.MapGet("/join", static async Task<Results<Ok<string>,ValidationProblem>>(string gameName, string playerKey, string name, [FromServices] GameService gameService,ValidationRules validationRules) =>
        {
            var game = gameService.GetGameByName(gameName);
            try{
                IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
                validationRules.JoinGameValidation(game,name,errors);
                if (errors.Any()) 
                {
                    return TypedResults.ValidationProblem(errors);
                }
                game.Join(name, playerKey);
            }finally{
            }
            return TypedResults.Ok(playerKey);
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Join the game with a display name";
            op.Description = "";
            return op;
        });

        group.MapGet("/start", static async Task<Results<Ok,ValidationProblem>>(string gameName, [FromServices] GameService gameService,ValidationRules validationRules) =>
        {
            var game = gameService.GetGameByName(gameName);
            try{

            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            validationRules.NotAlreadyStarted(game, errors);
            if (errors.Any())
            {
                return TypedResults.ValidationProblem(errors);
            }
            game.StartGame();
            }finally{
            }
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Starts the game";
            op.Description = "Starts the game. This will destroy any game in progress.";
            return op;
        });
        group.MapGet("/check-for-timeout", static async Task<Results<Ok,ValidationProblem>>(string gameName,[FromServices] GameService gameService,ValidationRules validationRules) =>
        {
            var game = gameService.GetGameByName(gameName);
            try{
                game.CheckForTimeout();
            }finally{
            }
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
