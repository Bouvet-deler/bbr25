using BoardGameServer.Application;
using Xunit;
using System;
using System.Collections.Generic;
using System.Linq;
namespace BoardGameServer.Tests.UnitTests
{
    public class GameServiceTests
    {

        //Følgende tester bør vi ha
        //-- Sett registrer div spillere
        //sjekker at rekkefølgen er lik
        //
        //
        [Fact]
        void StartGameWithOnePlayer_PlayerIsSetUp()
        {
            Game game = new Game();
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
            Assert.True(game.Deck.Count()>0);
        }
        [Fact]
        void StartGameWithTwoPlayers_PlayerTwoIsSetUp()
        {
            Game game = new Game();
            string name = "Bendert";
            game.Join("Først");
            game.Join(name);
            game.StartGame();
            Player p = game.Players.Where(s=> !s.StartingPlayer).FirstOrDefault();
            Assert.NotNull(p);
            Assert.False(p.StartingPlayer);
            Assert.True(p.Hand.Any());
            Assert.True(p.Fields.Any());
            Assert.True(p.Name == name);
        }
        [Fact]
        void StartGameWithThreePlayers_OnlyOneStartingPlayer()
        {
            Game game = new Game();
            string name = "Bendert";
            game.Join("Først");
            game.Join("Andre");
            game.Join(name);
            game.StartGame();
            Assert.NotNull(game.Players.Where(s=> s.StartingPlayer).Single());
            Assert.True(game.Players.Where(s=> !s.StartingPlayer).Count() == 2);

        }
        [Fact]
        void JoinGame_PlayerCountIncreases()
        {
            Game game = new Game();
            game.Join("Først");
            Assert.True(game.Players.Count() == 1);
            string name = "Bendert";
            game.Join(name);
            Assert.True(game.Players.Count() == 2);

        }
        [Fact]
        void JoinGame()
        {
            Game game = new Game();
            game.Join("Først");
            Assert.True(game.Players.Count() == 1);
            string name = "Bendert";
            game.Join(name);
            Assert.True(game.Players.Count() == 2);

        }
        [Fact]
        void GoToPlantingPhase_AddsCardsToHand()
        {
            Game game = new Game();
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
            Game game = new Game();
            game.Join("Først");
            string name = "Bendert";
            game.Join(name);
            game.Join("Luring");
            game.random = new Random(1);
            game.StartGame();
            Player p1 = game.Players.First();
            Player p2 = game.Players.Last();
            foreach(var card in p1.Hand)
            {
                Console.WriteLine(card.Type);
            }
            foreach(var card in p2.Hand)
            {
                Console.WriteLine(card.Type);
            }
            game.CurrentPlayer = p2;
            game.CurrentPhase = Phase.Trading;
            Card offeredCard = p2.Hand.Where(c=>c.Type == "ChiliBean").Last();
            Offer o = new Offer(new List<Card>{ offeredCard }, new List<string>());
            game.OfferTrade(o);
            game.AcceptTrade(p1, o.Id, new List<Guid>());
            
            Assert.True(p1.TradedCards.Contains(offeredCard));
            Assert.False(p2.Hand.Contains(offeredCard));
            Assert.True(p2.Hand.Contains(p2.Hand.Where(c=>c.Type == "ChiliBean").Last()));
        }
    }
}
