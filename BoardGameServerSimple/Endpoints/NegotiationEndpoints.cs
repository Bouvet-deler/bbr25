using BoardGameServerSimple.Services;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.AspNetCore.Mvc;
using Negotiator;
using Negotiator.Models;
using SharedModels;

namespace BoardGameServerSimple.Endpoints;

public static class NegotiationEndpoints
{

    //ToDo: All calls needs to be validated against the state of the Game. 
    public static IEndpointRouteBuilder MapNegotiationEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/negotiation");

        group.MapPost("/start-negotiation", static async Task<Results<Ok<NegotiationState>, NotFound>> ([FromBody] NegotiationRequest negotiationRequest, [FromServices] INegotiationService negotiationService, [FromServices] MessageValidator messageValidator) =>
        {
            NegotiationState response;

            //Server needs to validate the message from the player.
            if (messageValidator.Validate(negotiationRequest))
            {
                response = negotiationService.StartNegotiation(negotiationRequest);
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

        group.MapGet("/get-negotiation-status/{id:guid}", static async Task<Results<Ok<NegotiationState>, NotFound>> ([FromServices]  INegotiationService negotiationService, Guid id) =>
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

        group.MapPost("/respond-negotiation", static async Task<Results<Ok<StatusOfferRequest>, NotFound>> (ResponseToOfferRequest request, [FromServices] INegotiationService negotiationService, [FromServices] MessageValidator messageValidator) =>
        {
            //Valid card offered?
            if (messageValidator.Validate(request))
            {
                return TypedResults.NotFound();
            }

            var status = await negotiationService.RespondToNegotiationAsync(request);
            if (status == null)
            {
                return TypedResults.NotFound();
            }
            if(status.OfferStatus == OfferStatus.Accepted)
            {
                negotiationService.EndNegotiation(status);
            }   
            return TypedResults.Ok<StatusOfferRequest>(status);
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
