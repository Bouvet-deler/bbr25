using BoardGameServer.Application;
using Xunit;
using System;
using System.Collections.Generic;
using System.Linq;
using SharedModels;
using Negotiator;
using FakeItEasy;

namespace BoardGameServer.Tests.UnitTests;

public class GameServiceTests
{
    private readonly INegotiationService _negotiationService;
    private readonly SharedModels.Offer _negotiationRequest;


    public GameServiceTests()
    {
        _negotiationService = A.Fake<INegotiationService>();
        _negotiationRequest = new SharedModels.Offer(
            Guid.NewGuid(),
            Guid.NewGuid(),
            Guid.NewGuid(),
            [Card.ChiliBean()],
            [Card.BlackEyedBean()]
        );
    }

    [Fact]
    void StartGameWithOnePlayer_PlayerIsSetUp()
    {
        var game = new Game(_negotiationService);
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
        var game = new Game(_negotiationService);
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
        var game = new Game(_negotiationService);
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
        var game = new Game(_negotiationService);
        game.Join("Først");
        Assert.True(game.Players.Count() == 1);
        string name = "Bendert";
        game.Join(name);
        Assert.True(game.Players.Count() == 2);

    }
    [Fact]
    void JoinGame()
    {
        var game = new Game(_negotiationService);
        game.Join("Først");
        Assert.True(game.Players.Count() == 1);
        string name = "Bendert";
        game.Join(name);
        Assert.True(game.Players.Count() == 2);

    }
    [Fact]
    void GoToPlantingPhase_AddsCardsToHand()
    {
        var game = new Game(_negotiationService);
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
        var game = new Game(_negotiationService);
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
        Card offeredCard = p2.Hand.Where(c => c.Type == "BlackEyedBean").Last();
        Card wantedCard = p1.Hand.Where(c => c.Type == "GardenBean").Last();
        var negotiationRequest = new SharedModels.Offer(
            _negotiationRequest.InitiatorId,
            _negotiationRequest.ReceiverId,
            _negotiationRequest.NegotiationId,
            new List<Card> { offeredCard },
            new List<Card> { wantedCard }
        );
        game.OfferTrade(negotiationRequest);
        var (CurrentPlayerHand, OpponentPlayerHand) = game.AcceptTrade(p1, negotiationRequest.NegotiationId, negotiationRequest.CardsToExchange, negotiationRequest.CardsToReceive);

        Assert.Contains(wantedCard, CurrentPlayerHand);
        Assert.DoesNotContain(wantedCard, OpponentPlayerHand);
        Assert.Contains(offeredCard, OpponentPlayerHand);
        Assert.DoesNotContain(offeredCard, CurrentPlayerHand);
    }
}
