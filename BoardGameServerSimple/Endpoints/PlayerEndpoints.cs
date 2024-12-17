using BoardGameServerSimple.Models;
using BoardGameServerSimple.Services;
using Microsoft.AspNetCore.Http.HttpResults;

namespace BoardGameServerSimple.Endpoints;

public static class PlayerEndpoints
{
    public static IEndpointRouteBuilder MapPlayerEndpoints(this IEndpointRouteBuilder routes)
    {

        var group = routes.MapGroup("/api/player").WithTags(nameof(GameState));

        group.MapPost("/play-card", static async Task<Results<Ok<Card>, BadRequest>> (GameStateManager gameStateManager, Card card, CardValidator cardValidator) =>
        {
            if (cardValidator.Validate(card))
            {
                await gameStateManager.PlayCard(card);
                return TypedResults.Ok(card);
            }
            return TypedResults.BadRequest();
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves card from player to be played";
            op.Description = "This card needs to be validated against the state of the player to confirm that the player actually possesses that card.";
            return op;
        });

        group.MapGet("/score/{playerId}", (int playerId, GameStateManager gameStateManager) =>
        {
            var score = gameStateManager.GetPlayerScore(playerId);
            return TypedResults.Ok(score);
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Recieves the score for the given player";
            op.Description = "";
            return op;
        });

        return routes;
    }
}