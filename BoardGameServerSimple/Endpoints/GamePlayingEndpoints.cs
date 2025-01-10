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

        //Hva var dette?
        /* group.MapGet("/{id}", static async Task<Results<Ok, BadRequest, ValidationProblem>> (Guid player, Guid field, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) => */
        /* { */
        /*     IDictionary<string, string[]> errors = new Dictionary<string, string[]>(); */
        /*     var game = gameService.GetCurrentGame(); //Or with Id? */
        /*     Player p = game.Players.Where(c => c.Id == player).First(); */
        /*     game.Plant(field); */
        /*     game.HarvestField(p, field); */
        /*     return TypedResults.Ok(); */
        /* }) */
        /* .WithOpenApi(op => */
        /* { */
        /*     op.Summary = "Recieves a field from player to be planted"; */
        /*     op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card."; */
        /*     return op; */
        /* }); */

        group.MapPost("/plant", static async Task<Results<Ok, BadRequest, ValidationProblem>> (Guid player, Guid field, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {

            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            var game = gameService.GetCurrentGame();
            Player p = game.Players.Where(c => c.Id == player).First();
            validationRules.PlantingPhaseValidation(game, p, field, errors);
            if (errors.Any())
            {
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

        group.MapPost("/end-trading", static async Task<Results<Ok<string>, BadRequest, ValidationProblem>> (Guid player, NegotiationState negotiationState, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
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

        group.MapPost("/trade-plant", static async Task<Results<Ok<string>, BadRequest, ValidationProblem>> (Guid playerId, Guid cardId, Guid fieldId, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {

            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            var game = gameService.GetCurrentGame();
            Player p = game.Players.Where(c => c.Id == playerId).First();
            validationRules.TradePlantingPhaseValidation(game, p,cardId, fieldId, errors);
            if (errors.Any()) 
            {
                return TypedResults.ValidationProblem(errors);
            }

            Card card = p.DrawnCards.Where(c=> c.Id == cardId).Union(p.TradedCards.Where(c=>c.Id == cardId)).Single();
            game.PlantTrade(p, card, fieldId);
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
            game.HarvestField(p, field);
            return TypedResults.Ok();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });


        group.MapPost("/start-negotiation", static async Task<Results<Ok<NegotiationState>, NotFound, ValidationProblem>> (Guid player, [FromBody] Offer negotiationRequest, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules, [FromServices] NegotiationService negotiationService) =>
        {
            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            NegotiationState response;
            var game = gameService.GetCurrentGame();

            Player p = game.Players.Where(c => c.Id == player).First();
            validationRules.StartNegotiationValidation(game,p, negotiationRequest, errors);
            //Are the game in the right state?
            //Server needs to validate the message from the player.
            if (errors.Any())
            {
                return TypedResults.ValidationProblem(errors);
            }

            negotiationService.StartNegotiation(negotiationRequest);
            response = new NegotiationState(Guid.NewGuid(), negotiationRequest.InitiatorId, negotiationRequest.ReceiverId, new List<Card>(), new List<string>());
            return TypedResults.Ok(response);
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves card from player to be played";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapGet("/get-negotiation-status", static async Task<Results<Ok<NegotiationState>, NotFound<ErrorResponse>>> ([FromServices] INegotiationService negotiationService) =>
        {
            //Any negotiatins ongoing with id == id?
            var status = negotiationService.GetNegotiationStatus();
            if (status.negotiationState is null || status.negotiationState.IsActive == false)
            {
                return TypedResults.NotFound(new ErrorResponse("Negotiation not found"));
            }

            //ToDo: Refactor to return a DTO
            return TypedResults.Ok(status.negotiationState);
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Gets the current status of an ongoing negotiation with ID.";
            op.Description = "Gets the current status of an ongoing negotiation. If there is no ongoing negotiation with the given Id an error message is returned.";
            return op;
        });

        group.MapPost("/negotiation", static async Task<Results<Ok, NotFound, ValidationProblem>> (Guid player, Offer request, [FromServices] INegotiationService negotiationService, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {

            //ToDo: Branch for iniator and rciever



            var game = gameService.GetCurrentGame();
            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            //Valid card offered?
            Player p = game.Players.Where(c => c.Id == player).First();
            validationRules.NegotiationValidation(game, p, request, errors);

            if (errors.Any())
            {
                return TypedResults.ValidationProblem(errors);
            }

            var status = negotiationService.RegisterOffer(request);
            //ToDo: Get player
            //if (status. == OfferStatus.Accepted)
            //{
            //    game.AcceptTrade(p,status.CardsGiven.Select(card=>card.Id).ToList(), status.CardsReceived.Select(card => card.Id).ToList());
            //}
            return TypedResults.Ok();
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
        return new NegotiationState(status.NegotiationId, status.InitiatorId, status.ReceiverId, status.CardsGiven, status.CardsReceived.Select(card => card.Type).ToList())
        {
            OfferAccepted = status.OfferStatus == ProposalStatus.Accepted,
            IsActive = false
        };
    }
}
