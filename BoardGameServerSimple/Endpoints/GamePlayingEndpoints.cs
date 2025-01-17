using Microsoft.AspNetCore.Http.HttpResults;
using SharedModels;
using BoardGameServer.Application.Services;
using Microsoft.AspNetCore.Mvc;
using Negotiator.Models;
using BoardGameServer.Application.Models;

namespace BoardGameServerSimple.Endpoints;

public static class GamePlayingEndpoints
{
    public static IEndpointRouteBuilder MapPlayerEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/playing");

        group.MapGet("/{id:guid}", static async Task<Results<Ok<PlayerStatus>, NotFound>> (Guid playerId, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {
            var game = gameService.GetGameByName(gameName);
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


        group.MapGet("/plant", static async Task<Results<Ok<string>, BadRequest, ValidationProblem>> (string gameName,Guid playerId, Guid fieldId, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {

            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            var game = gameService.GetGameByName(gameName);
            game.Lock.Enter();
            Player p = game.Players.Where(c => c.Id == playerId).First();
            validationRules.PlantingPhaseValidation(game, p, fieldId, errors);
            if (errors.Any())
            {
                Console.WriteLine("Ikke plantet");
                game.Lock.Exit();
                return TypedResults.ValidationProblem(errors);
            }
            game.Plant(fieldId);
            game.Lock.Exit();
            return TypedResults.Ok("plantet");
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves which field the card in their hand should be planted to";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapGet("/end-planting", static async Task<Results<Ok<string>, BadRequest, ValidationProblem>> (string gameName,Guid playerId, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {
            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            var game = gameService.GetGameByName(gameName);
            game.Lock.Enter();
            Player p = game.Players.Where(c => c.Id == playerId).First();
            validationRules.EndPlantingValidation(game, p, errors);
            if (errors.Any()) {
            game.Lock.Exit();
                return TypedResults.ValidationProblem(errors);
            }
            game.EndPlanting();
            game.Lock.Exit();
            return TypedResults.Ok("Plantefase avsluttet");
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "May fail if the card is not plantable in the field";
            return op;
        });

        group.MapGet("/end-trading", static async Task<Results<Ok<string>, BadRequest, ValidationProblem>> (string gameName,Guid playerId, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {
            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            var game = gameService.GetGameByName(gameName);
            game.Lock.Enter();
            Player p = game.Players.Where(c => c.Id == playerId).First();
            validationRules.EndTradingValidation(game, p, errors);
            if (errors.Any()) 
            {
            game.Lock.Exit();
                return TypedResults.ValidationProblem(errors);
            }
            game.EndTrading();
            game.Lock.Exit();
            return TypedResults.Ok("Trading-fase avsluttet");
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapGet("/trade-plant", static async Task<Results<Ok<string>, BadRequest, ValidationProblem>> (string gameName, Guid playerId, Guid cardId, Guid fieldId, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {

            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            var game = gameService.GetGameByName(gameName);
            game.Lock.Enter();
            Player p = game.Players.Where(c => c.Id == playerId).First();
            validationRules.TradePlantingPhaseValidation(game, p,cardId, fieldId, errors);
            if (errors.Any()) 
            {
                Console.WriteLine("Validation traee planting");
            game.Lock.Exit();
                return TypedResults.ValidationProblem(errors);
            }

            Card card = p.DrawnCards.Where(c=> c.Id == cardId).Union(p.TradedCards.Where(c=>c.Id == cardId)).Single();
            game.PlantTrade(p, card, fieldId);
            Console.WriteLine("Suksee tradeplant");
            game.Lock.Exit();
            return TypedResults.Ok("Plantet etter byttene");
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapGet("/harvest-field", static async Task<Results<Ok<string>, ValidationProblem>> (string gameName, Guid playerId, Guid fieldId, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {
            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            var game = gameService.GetGameByName(gameName);
            game.Lock.Enter();
            Player p = game.Players.Where(c => c.Id == playerId).First();
            validationRules.HarvestFieldValidation(game, p, fieldId, errors);
            if (errors.Any()) {
            Console.WriteLine("Funker denne");
            game.Lock.Exit();
                return TypedResults.ValidationProblem(errors);
            }
            game.HarvestField(p, fieldId);
            game.Lock.Exit();
            return TypedResults.Ok("Høstet suksessfylt");
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves a field from player to be planted";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapPost("/request-trade", static async Task<Results<Ok<string>, NotFound<ErrorResponse>>> (string gameName, Guid playerId, [FromBody]OfferDto offer, [FromServices] GameService gameService) =>
        {
            var game = gameService.GetGameByName(gameName);
            game.Lock.Enter();
            //finn kortene som skal med i offer

            Player p = game.Players.Where(c => c.Id == playerId).First();
            var cards = p.DrawnCards.Union(p.Hand).Where(c=> offer.OfferedCards.Any(c1 => c1 == c.Id)).ToList();
            var realOffer = new Offer(playerId, cards, offer.CardTypesWanted);
            game.RequestTrade(realOffer);
            game.Lock.Exit();
            return TypedResults.Ok("Bytte blir preentert!");
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Gets the current status of an ongoing negotiation with ID.";
            op.Description = "Gets the current status of an ongoing negotiation. If there is no ongoing negotiation with the given Id an error message is returned.";
            return op;
        });

        group.MapPost("/accept-trade", static async Task<Results<Ok<string>, NotFound, ValidationProblem>> (string gameName, Guid playerId, [FromBody]Accept accept, [FromServices] GameService gameService, [FromServices] ValidationRules validationRules) =>
        {
            var game = gameService.GetGameByName(gameName);
            game.Lock.Enter();
            IDictionary<string, string[]> errors = new Dictionary<string, string[]>();
            //Valid card offered?
            Player accepter = game.Players.Where(c => c.Id == playerId).First();
            var status = game.TradingArea.SingleOrDefault(offer => offer.NegotiationId == accept.NegotiationId);
            if (status == null)
            {
            game.Lock.Exit();
                return TypedResults.NotFound();
            }
            Player initiator = game.Players.Where(c => c.Id == status.InitiatorId).First();

            validationRules.AcceptTradeValidation(game, accepter,status, accept, errors);

            if (errors.Any())
            {
                
            game.Lock.Exit();
                return TypedResults.ValidationProblem(errors);
            }

            game.TradingArea.Remove(status);
            game.AcceptTrade(initiator, accepter,status.OfferedCards.Select(s=>s.Id).ToList(), accept.Payment);
            game.Lock.Exit();
            return TypedResults.Ok("Bytte utført");
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Responds to an ongoing negotiation.";
            op.Description = "Responds to an ongoing negotiation. If there is no ongoing negotiation with the given Id an error message is returned.";
            return op;
        });

        return routes;
    }

}
