using BoardGameServer.Application.Services;
using BoardGameServerSimple.Endpoints;
using ScoringService;
using Negotiator;
using Scalar.AspNetCore;

var builder = WebApplication.CreateBuilder(args);
var MyAllowSpecificOrigins = "_myAllowSpecificOrigins";
// Add services to the container.
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();
builder.Services.AddSingleton<ValidationRules>();
builder.Services.AddSingleton<GameService>();
builder.Services.AddSingleton<INegotiationService, NegotiationService>();
builder.Services.AddSingleton<EloCalculator, EloCalculator>();
builder.Services.AddSingleton<IScoreRepository, ScoreRepository>();
/* builder.Services.AddSingleton<IScoreRepository, AzureScoreRepository>(); */

builder.Services.AddCors(options =>
{
    options.AddPolicy(name: MyAllowSpecificOrigins,
                      policy =>
                      {
                          policy.WithOrigins("http://localhost:5173");
                      });
});

var app = builder.Build();

app.MapOpenApi();
app.MapGameBoardEndpoints();
app.MapScoreBoardEndpoints();
app.MapPlayerEndpoints();

app.MapScalarApiReference(options =>
{
    options
    .WithTitle("Board Game Server")
    .WithTheme(ScalarTheme.Mars)
    .WithDefaultHttpClient(ScalarTarget.CSharp, ScalarClient.HttpClient);
});


app.UseHttpsRedirection();
app.UseCors(MyAllowSpecificOrigins);
app.Run();
