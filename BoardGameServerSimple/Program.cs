using BoardGameServerSimple.Endpoints;
using BoardGameServerSimple.Models;
using BoardGameServerSimple.Services;
using Scalar.AspNetCore;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();
builder.Services.AddSingleton<GameStateManager>();
builder.Services.AddSingleton<GameStateFactory>();
builder.Services.AddSingleton<CardValidator>();
builder.Services.AddSingleton<CommunicationManager>();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.MapGameBoardEndpoints();
    app.MapPlayerEndpoints();
    app.MapCommunicationEndpoints();

    app.MapScalarApiReference(options =>
    {
        options
        .WithTitle("Board Game Server")
        .WithTheme(ScalarTheme.Mars)
        .WithDefaultHttpClient(ScalarTarget.CSharp, ScalarClient.HttpClient);
    });
}

// Communication Endpoints
app.MapPost("/api/message/send", (string message, CommunicationManager communicationManager) =>
{
    communicationManager.SendMessage(message);
    return Results.Ok();
});

app.MapGet("/api/message/receive", (CommunicationManager communicationManager) =>
{
    var messages = communicationManager.ReceiveMessages();
    return Results.Ok(messages);
});



app.UseHttpsRedirection();
app.Run();
