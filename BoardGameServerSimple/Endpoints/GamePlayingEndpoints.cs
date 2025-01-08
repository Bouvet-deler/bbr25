using BoardGameServerSimple.Services;
using BoardGameServer.Application;
using Microsoft.AspNetCore.Http.HttpResults;
using SharedModels;
using BoardGameServer.Application.Services;
using Microsoft.AspNetCore.Mvc;
using Negotiator.Models;
using Negotiator;

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

        group.MapGet("/{id}", static async Task<Results<Ok, BadRequest>> (string player, Guid field, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {
            var game = gameService.GetCurrentGame(); //Or with Id?
            Guid playerKey;
            if (!Guid.TryParse(player, out playerKey));
            Player p = game.Players.Where(c => c.Id == playerKey).First();
            game.HarvestField(p, field);
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapPost("/end-planting", static async Task<Results<Ok<string>, BadRequest>> (string playerKey, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {
            var game = gameService.GetCurrentGame();
            game.EndPlanting();
            return TypedResults.BadRequest();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapPost("/plant", static async Task<Results<Ok, BadRequest, ValidationProblem>> (Guid player, Guid field, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {

            var game = gameService.GetCurrentGame();
            Player p = game.Players.Where(c => c.Id == player).First();
            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            validationRules.PlantingPhaseValidation(game, p, field, errors);
            return TypedResults.ValidationProblem(errors);
            game.Plant(field);
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapPost("/harvest-field", static async Task<Results<Ok, BadRequest>> (Guid player, Guid field, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {
            var game = gameService.GetCurrentGame();
            Player p = game.Players.Where(c => c.Id == player).First();
            game.HarvestField(p, field);
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });


        group.MapPost("/start-negotiation", static async Task<Results<Ok<NegotiationState>, NotFound>> ([FromBody] NegotiationRequest negotiationRequest, [FromServices] GameService gameService, [FromServices] MessageValidator messageValidator) =>
        {
            NegotiationState response;
            var game = gameService.GetCurrentGame();

            //Are the game in the right state?
            //Server needs to validate the message from the player.
            if (messageValidator.Validate(negotiationRequest))
            {
                //The id of the response needs to be stored in the game state for others to query it.
                response = game.OfferTrade(negotiationRequest);
                return TypedResults.Ok(response);
            }
            return TypedResults.NotFound();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves card from player to be played";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapGet("/get-negotiation-status/{id:guid}", static async Task<Results<Ok<NegotiationState>, NotFound>> ([FromServices] INegotiationService negotiationService, Guid id) =>
        {
            //Any negotiatins ongoing with id == id?
            var status = negotiationService.GetNegotiationStatus(id);
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

        group.MapPost("/negotiation", static async Task<Results<Ok<ResultOfferRequest>, NotFound>> (ResponseToOfferRequest request, [FromServices] INegotiationService negotiationService, [FromServices] GameService gameService, [FromServices] MessageValidator messageValidator) =>
        {
            var game = gameService.GetCurrentGame();
            //Valid card offered?
            if (messageValidator.Validate(request))
            {
                return TypedResults.NotFound();
            }

                //var status = await negotiationService.RespondToNegotiationAsync(request);
                //ToDo: Get player
                var status = await game.Negotiate(request);
                if (status == null)
                {
                    return TypedResults.NotFound();
                }
                if (status.OfferStatus == OfferStatus.Accepted)
                {
                    NegotiationState negotiationState = CreateFinalnegotiationState(status);
                    negotiationService.EndNegotiation(negotiationState);
                    game.EndTrading(negotiationState);
                }
                return TypedResults.Ok<ResultOfferRequest>(status);
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Responds to an ongoing negotiation.";
            op.Description = "Responds to an ongoing negotiation. If there is no ongoing negotiation with the given Id an error message is returned.";
            return op;
        });

        return routes;
    }

    private static NegotiationState CreateFinalnegotiationState(ResultOfferRequest status)
    {
        return new NegotiationState(status.NegotiationId, status.InitiatorId, status.ReceiverId, status.CardsExchanged, status.CardsReceived)
        {
            OfferAccepted = status.OfferStatus == OfferStatus.Accepted,
            IsActive = false
        };
    }
}
