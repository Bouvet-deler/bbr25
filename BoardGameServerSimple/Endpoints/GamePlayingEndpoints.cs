using BoardGameServer.Application;
using Microsoft.AspNetCore.Http.HttpResults;
using SharedModels;
using BoardGameServer.Application.Services;
using Microsoft.AspNetCore.Mvc;

namespace BoardGameServerSimple.Endpoints;

public static class GamePlayingEndpoints
{
    public static IEndpointRouteBuilder MapPlayerEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/playing");

        group.MapGet("/{id:guid}", static async Task<Results<Ok<PlayerStatus>, NotFound>> (Guid playerId, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {
            var game = gameService.GetCurrentGame();
            var status = gameService.GetStatusPlayer(playerId);
            if (status == null)
            {
                return TypedResults.NotFound();
            }

            return TypedResults.Ok(status);
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Gets the current status of an ongoing negotiation with ID.";
            op.Description = "Gets the current status of an ongoing negotiation. If there is no ongoing negotiation with the given Id an error message is returned.";
            return op;
        });

        group.MapGet("/{id}", static async Task<Results<Ok, BadRequest, ValidationProblem>> (Guid player, Guid field, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {
            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            var game = gameService.GetCurrentGame(); //Or with Id?
            Player p = game.Players.Where(c => c.Id == player).First();
            game.Plant(field);
            game.HarvestField(p, field);
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapPost("/plant", static async Task<Results<Ok, BadRequest, ValidationProblem>> (Guid player, Guid field, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {

            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            var game = gameService.GetCurrentGame();
            Player p = game.Players.Where(c => c.Id == player).First();
            validationRules.PlantingPhaseValidation(game, p, field, errors);
            if (errors.Any()) {
                return TypedResults.ValidationProblem(errors);
            }
            game.Plant(field);
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves which field the card in their hand should be planted to";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapPost("/end-planting", static async Task<Results<Ok<string>, BadRequest, ValidationProblem>> (Guid player, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {

            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            var game = gameService.GetCurrentGame();
            Player p = game.Players.Where(c => c.Id == player).First();
            validationRules.EndPlantingValidation(game, p, errors);
            if (errors.Any()) {
                return TypedResults.ValidationProblem(errors);
            }
            game.EndPlanting();
            return TypedResults.BadRequest();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapPost("/end-trading", static async Task<Results<Ok<string>, BadRequest, ValidationProblem>> (Guid player, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {

            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            var game = gameService.GetCurrentGame();
            Player p = game.Players.Where(c => c.Id == player).First();
            validationRules.EndTradingValidation(game, p, errors);
            if (errors.Any()) 
            {
                return TypedResults.ValidationProblem(errors);
            }
            game.EndTrading();
            return TypedResults.BadRequest();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapPost("/trade-plant", static async Task<Results<Ok<string>, BadRequest, ValidationProblem>> (Guid player, Guid card, Guid field, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {

            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            var game = gameService.GetCurrentGame();
            Player p = game.Players.Where(c => c.Id == player).First();
            validationRules.TradePlantingPhaseValidation(game, p,card, field, errors);
            if (errors.Any()) 
            {
                return TypedResults.ValidationProblem(errors);
            }
            game.EndTrading();
            return TypedResults.BadRequest();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapPost("/harvest-field", static async Task<Results<Ok, BadRequest, ValidationProblem>> (Guid player, Guid field, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {
            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            var game = gameService.GetCurrentGame();
            Player p = game.Players.Where(c => c.Id == player).First();
            validationRules.HarvestFieldValidation(game, p, field, errors);
            if (errors.Any()) {
                return TypedResults.ValidationProblem(errors);
            }
            game.Plant(field);
            game.HarvestField(p, field);
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        return routes;
    }
}
