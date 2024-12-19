using BoardGameServerSimple.Services;
using Microsoft.AspNetCore.Http.HttpResults;

namespace BoardGameServerSimple.Endpoints;

public static class CommunicationEndpoints
{
    public static IEndpointRouteBuilder MapCommunicationEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/message");


        group.MapPost("/send-message", static async Task<Results<Ok, NotFound>> (CommunicationManager communicationManager, string message, MessageValidator messageValidator) =>
        {
            if (messageValidator.Validate(message))
            {
                await communicationManager.SendMessage(message);
            }
            return TypedResults.NotFound();
        })
.WithOpenApi(op =>
{
    op.Summary = "Recieves card from player to be played";
    op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
    return op;
});

        //Webhooks

        return routes;
    }
 
}
