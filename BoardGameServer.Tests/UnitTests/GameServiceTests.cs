using BoardGameServer.Application;
using Xunit;
using System;
using System.Collections.Generic;
using System.Linq;
using SharedModels;
using Negotiator;
using FakeItEasy;
using ScoringService;
using BoardGameServer.Application.Models;

namespace BoardGameServer.Tests.UnitTests;

public class GameServiceTests
{
    private readonly INegotiationService _negotiationService;

    private readonly IScoreRepository _scoreRepository;
    private readonly EloCalculator _eloCalculator;

    public GameServiceTests()
    {
        _scoreRepository = new ScoreRepository();
        _eloCalculator = new EloCalculator(_scoreRepository);
        _negotiationService = A.Fake<INegotiationService>();

    }

    //Følgende tester bør vi ha
    //-- Sett registrer div spillere
    //sjekker at rekkefølgen er lik
    //
    //
    [Fact]
    void StartGameWithOnePlayer_PlayerIsSetUp()
    {
        Game game = new Game( _eloCalculator);
        string name = "Bendert";
        string playerId = Guid.NewGuid().ToString();
        game.Join(name, playerId);
        game.StartGame();
        Player p = game.Players.FirstOrDefault();
        Assert.NotNull(p);
        Assert.True(p.StartingPlayer);
        Assert.True(p.Hand.Any());
        Assert.True(p.Fields.Any());
        Assert.True(p.Fields.Any());
        Assert.True(p.Name == name);
        Assert.True(game.Deck.Count() > 0);
    }

    [Fact]
    void StartGameWithTwoPlayers_PlayerTwoIsSetUp()
    {
        Game game = new Game( _eloCalculator);
        string name = "Bendert";
        string playerId = Guid.NewGuid().ToString();
        game.Join("Først", Guid.NewGuid().ToString());
        game.Join(name, playerId);
        game.StartGame();
        Player p = game.Players.Where(s => !s.StartingPlayer).FirstOrDefault();
        Assert.NotNull(p);
        Assert.False(p.StartingPlayer);
        Assert.True(p.Hand.Any());
        Assert.True(p.Fields.Any());
    }
    [Fact]
    void StartGameWithThreePlayers_OnlyOneStartingPlayer()
    {
        Game game = new Game( _eloCalculator);
        string name = "Bendert";
        string playerId = Guid.NewGuid().ToString();
        game.Join("Først", Guid.NewGuid().ToString());
        game.Join("Andre", Guid.NewGuid().ToString());
        game.Join(name, playerId);
        game.StartGame();
        Assert.NotNull(game.Players.Where(s => s.StartingPlayer).Single());
        Assert.True(game.Players.Where(s => !s.StartingPlayer).Count() == 2);

    }
    [Fact]
    void JoinGame_PlayerCountIncreases()
    {
        Game game = new Game( _eloCalculator);
        game.Join("Først", Guid.NewGuid().ToString());
        Assert.True(game.Players.Count() == 1);
        string name = "Bendert";
        string playerId = Guid.NewGuid().ToString();
        game.Join(name, playerId);
        Assert.True(game.Players.Count() == 2);

    }
    [Fact]
    void JoinGame()
    {
        Game game = new Game( _eloCalculator);
        game.Join("Først", Guid.NewGuid().ToString());
        Assert.True(game.Players.Count() == 1);
        string name = "Bendert";
        string playerId = Guid.NewGuid().ToString();
        game.Join(name, playerId);
        game.StartGame();
        Assert.True(game.Players.Count() == 2);
        Player player = game.Players.First();
        Player player2 = game.Players[1];
        Assert.True(player == player.NextPlayer.NextPlayer);
        Assert.True(player2 == player.NextPlayer.NextPlayer.NextPlayer);
        var next = player.NextPlayer;
        Assert.True(player == next.NextPlayer.NextPlayer.NextPlayer);
    }
    [Fact]
    void GoToPlantingPhase_AddsCardsToHand()
    {
        Game game = new Game( _eloCalculator);
        game.Join("Først", Guid.NewGuid().ToString());
        string name = "Bendert";
        string playerId = Guid.NewGuid().ToString();
        game.Join(name, playerId);
        game.StartGame();
        Assert.True(game.Deck.Count() > 3);
        Player p = game.Players.First();
        int cardsIHand = p.Hand.Count();
        game.GoToPlantingPhase();

        Assert.True(p.Hand.Count() == cardsIHand + 3);

    }
    [Fact]
    void Trade_TradeAwayLastChilibean_LastChilibeanRemoved()
    {
        Game game = new Game( _eloCalculator);
        game.Join("Først", Guid.NewGuid().ToString());
        string name = "Bendert";
        string playerId = Guid.NewGuid().ToString();
        game.Join(name, playerId);
        game.Join("Luring", Guid.NewGuid().ToString());
        game.random = new Random(1);
        game.StartGame();
        Player p1 = game.Players.First();
        Player p2 = game.Players.Last();
        foreach (var card in p1.Hand)
        {
            Console.WriteLine(card.Type);
        }
        foreach (var card in p2.Hand)
        {
            Console.WriteLine(card.Type);
        }
        game.CurrentPlayer = p2;
        game.CurrentPhase = Phase.Trading;
        Card offeredCard = p2.Hand.Where(c => c.Type == "ChiliBean").Last();
        Offer offer = new Offer(game.CurrentPlayer.Id, new List<Card> { offeredCard }, new List<string>());
        _negotiationService.StartNegotiation(offer);
        game.AcceptTrade(game.CurrentPlayer, p1, offer.OfferedCards.Select(s=>s.Id).ToList(), new List<Guid>());

        Assert.Contains(offeredCard, p1.TradedCards);
        Assert.False(p2.Hand.Contains(offeredCard));
        Assert.True(p2.Hand.Contains(p2.Hand.Where(c => c.Type == "ChiliBean").Last()));
    }
}