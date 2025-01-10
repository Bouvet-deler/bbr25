using BoardGameServer.Application;
using Xunit;
using System;
using System.Collections.Generic;
using System.Linq;
using SharedModels;
using Negotiator;
using FakeItEasy;
using ScoringService;

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
        Game game = new Game(_negotiationService, _eloCalculator);
        string name = "Bendert";
        game.Join(name);
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
        Game game = new Game(_negotiationService, _eloCalculator);
        string name = "Bendert";
        game.Join("Først");
        game.Join(name);
        game.StartGame();
        Player p = game.Players.Where(s => !s.StartingPlayer).FirstOrDefault();
        Assert.NotNull(p);
        Assert.False(p.StartingPlayer);
        Assert.True(p.Hand.Any());
        Assert.True(p.Fields.Any());
        Assert.True(p.Name == name);
    }
    [Fact]
    void StartGameWithThreePlayers_OnlyOneStartingPlayer()
    {
        Game game = new Game(_negotiationService, _eloCalculator);
        string name = "Bendert";
        game.Join("Først");
        game.Join("Andre");
        game.Join(name);
        game.StartGame();
        Assert.NotNull(game.Players.Where(s => s.StartingPlayer).Single());
        Assert.True(game.Players.Where(s => !s.StartingPlayer).Count() == 2);

    }
    [Fact]
    void JoinGame_PlayerCountIncreases()
    {
        Game game = new Game(_negotiationService, _eloCalculator);
        game.Join("Først");
        Assert.True(game.Players.Count() == 1);
        string name = "Bendert";
        game.Join(name);
        Assert.True(game.Players.Count() == 2);

    }
    [Fact]
    void JoinGame()
    {
        Game game = new Game(_negotiationService, _eloCalculator);
        game.Join("Først");
        Assert.True(game.Players.Count() == 1);
        string name = "Bendert";
        game.Join(name);
        Assert.True(game.Players.Count() == 2);

    }
    [Fact]
    void GoToPlantingPhase_AddsCardsToHand()
    {
        Game game = new Game(_negotiationService, _eloCalculator);
        game.Join("Først");
        string name = "Bendert";
        game.Join(name);
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
        Game game = new Game(_negotiationService, _eloCalculator);
        game.Join("Først");
        string name = "Bendert";
        game.Join(name);
        game.Join("Luring");
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
        Offer offer = new Offer(game.CurrentPlayer.Id, p1.Id, Guid.NewGuid(), new List<Card> { offeredCard }, new List<string>());
        _negotiationService.StartNegotiation(offer);
        game.AcceptTrade(p1, offer.OfferedCards.Select(card => card.Id).ToList(), new List<Guid>());

        Assert.Contains(offeredCard, p1.TradedCards);
        Assert.False(p2.Hand.Contains(offeredCard));
        Assert.True(p2.Hand.Contains(p2.Hand.Where(c => c.Type == "ChiliBean").Last()));
    }
}