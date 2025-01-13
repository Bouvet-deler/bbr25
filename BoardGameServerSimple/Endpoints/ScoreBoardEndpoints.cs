using BoardGameServer.Application;
using BoardGameServer.Application.Services;
using ScoringService;
using SharedModels;
using Microsoft.AspNetCore.Mvc;
namespace BoardGameServerSimple.Endpoints;

public static class ScoreBoardEndpoints
{
    public static IEndpointRouteBuilder MapScoreBoardEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/score");

        group.MapGet("/get", ( [FromServices] IScoreRepository scoreRepository) =>
        {
            var result = scoreRepository.GetScores();
            return TypedResults.Ok(result);
        })
        .WithOpenApi(op =>
        {
            op.Summary = "Gets Gets all the scores of the game";
            op.Description = "";
            return op;
        });

        return routes;
    }
}
