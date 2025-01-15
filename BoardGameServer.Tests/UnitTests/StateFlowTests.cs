using BoardGameServer.Application;
using Xunit;
using System.Linq;
using System;
using System.Collections.Generic;
using SharedModels;
using ScoringService;
using FakeItEasy;
using BoardGameServer.Application.Models;

namespace BoardGameServer.Tests.UnitTests;

public class StateFlowTests
{

    private readonly IScoreRepository _scoreRepository;
    private readonly EloCalculator _eloCalculator;

    public StateFlowTests()
    {
        _scoreRepository = new ScoreRepository();
        _eloCalculator = new EloCalculator(_scoreRepository);
    }

    [Fact]
    public void PlantWhenInPlantingPhaseTakesYouToPlantingOptional()
    {
        Game game = new Game(_eloCalculator);
        game.Join("Benny");
        game.Join("Benny");
        game.StartGame();
        game.CurrentPhase = Phase.Planting;
        Guid field = game.CurrentPlayer.Fields.Keys.First();
        game.Plant(field);
        Assert.True(game.CurrentPhase == Phase.PlantingOptional);

    }
    [Fact]
    public void PlantWhenInPlantingOptionalTakesYouToTrading()
    {
        Game game = new Game(_eloCalculator);
        game.Join("Benny");
        game.Join("Benny");
        game.StartGame();
        game.CurrentPhase = Phase.PlantingOptional;
        Guid field = game.CurrentPlayer.Fields.Keys.First();

        game.Plant(field);
        Assert.True(game.CurrentPhase == Phase.Trading);

    }
    [Fact]
    public void EndPlantingInPlantingOptionalTakesYouToTrading()
    {
        Game game = new Game(_eloCalculator);
        game.Join("Benny");
        game.Join("Benny");
        game.StartGame();
        game.CurrentPhase = Phase.PlantingOptional;


        game.EndPlanting();
        Assert.True(game.CurrentPhase == Phase.Trading);
    }

    [Fact]
    public void EndTradingInPlantingOptionalTakesYouToTradePlanting()
    {
        Game game = new Game(_eloCalculator);
        game.Join("Benny");
        game.Join("Benny");
        game.StartGame();
        game.CurrentPhase = Phase.Trading;


        game.EndTrading();
        Assert.True(game.CurrentPhase == Phase.TradePlanting);
    }

    //Følgene er bare lov om man ikke har et gyldig kort og spille.
    //Vi eksponerer tomme turer fordi jeg antar klientene kan bli dummere av det
    [Fact]
    public void EndPlantingInPlantingTakesYouToTrading()
    {
        Game game = new Game(_eloCalculator);
        game.Join("Benny");
        game.Join("Benny");
        game.StartGame();
        game.CurrentPhase = Phase.Planting;

        game.EndPlanting();

        Assert.True(game.CurrentPhase == Phase.Trading);
    }
    //Denne testen kom før vi faktisk kan plante kort, så tar ikke høyde for at det
    //skjer noe med hånda til spiller
    [Fact]
    public void PlantTradeFinalCallMakesItTheNextPlayersTurn()
    {
        Game game = new Game(_eloCalculator);
        game.Join("Benny");
        game.Join("Benny");
        game.StartGame();
        game.CurrentPhase = Phase.TradePlanting;
        Player p1 = game.Players.First();
        Player p2 = game.Players.Last();
        Card card = Card.ChiliBean();
        p1.TradedCards.Add(card); 
        Guid field1 = p1.Fields.Keys.First();
        Guid field2 = p2.Fields.Keys.First();

        game.PlantTrade(p1, card, field1);

        Assert.True(game.CurrentPhase == Phase.Planting);
        Assert.True(game.CurrentPlayer == p2);

        p2.TradedCards.Add(card); 
        game.CurrentPhase = Phase.TradePlanting;
        game.PlantTrade(p2,card, field2);
        Assert.True(game.CurrentPhase == Phase.Planting);
        Assert.True(game.CurrentPlayer == p1);
    }

    [Fact]
    public void GameRoundTwoPlayers_PlantInFirstField()
    {
        int numCards = 104;
        Game game = new Game(_eloCalculator);
        game.Join("Benny");
        game.Join("Bjørn");
        game.StartGame();
        Player p1 = game.Players[0];
        Player p2 = game.Players[1];
        Assert.True(p1.StartingPlayer);
        numCards -= 10; // 5 per spiller

        Guid fieldP1 = p1.Fields.Keys.First();
        game.Plant(fieldP1);
        game.EndPlanting();
        game.EndTrading();
        numCards -= 2; // 2 avdekkes
        Assert.True(game.Deck.Count() == numCards);
        while (p1.DrawnCards.Any())
        {
            var card = p1.DrawnCards.First();
            game.PlantTrade(p1, card, fieldP1);

        }
        numCards -= 3; // 3 trekkes av spiller
        Assert.True(game.Deck.Count() == numCards);
        Assert.True(game.CurrentPlayer == p2);
        Assert.True(p2.Name == "Bjørn");
        Guid fieldP2 = p2.Fields.Keys.First();
        game.Plant(fieldP2);
        game.Plant(fieldP2);
        List<Card> offer = new List<Card>() {p2.DrawnCards.First()};
        List<Card> handList = p1.Hand.ToList();
        List<Card> price = new List<Card>() {
            handList[0],
            handList[1],
            handList[2],
            handList[3]
        };
        var trade = new Offer(p1.Id, offer.Select(c=>c.Id).ToList(), price.Select(p => p.Type).ToList());

        var guids = offer.Select(o=>o.Type).ToList();
        Assert.True(game.CurrentPlayer == p2);
        game.AcceptTrade(p1, trade.OfferedCards, price.Select(s=>s.Id).ToList());
        game.EndTrading();
        while (p1.DrawnCards.Any())
        {
            var card = p1.DrawnCards.First();
            game.PlantTrade(p1, card, fieldP1);
        }
        while (p1.TradedCards.Any())
        {
            var card = p1.TradedCards.First();
            game.PlantTrade(p1, card, fieldP1);
        }
        while (p2.DrawnCards.Any())
        {
            var card = p2.DrawnCards.First();
            game.PlantTrade(p2, card, fieldP2);
        }
        while (p2.TradedCards.Any())
        {
            var card = p2.TradedCards.First();
            game.PlantTrade(p2, card, fieldP2);
        }
        numCards -= 5; //5 kort spilles på en runde
        Assert.True(game.CurrentPhase == Phase.Planting);
        Assert.True(game.Deck.Count() == numCards);
    }
    [Fact]
    public void GameRoundTwoPlayers_HilmarActuallyPlays()
    {
        int numCards = 104;
        Game game = new Game(_eloCalculator);
        game.Join("Albert");
        game.Join("Bjørn");
        game.Join("Catrin");
        game.random = new Random(1);
        game.StartGame();
        Player albert = game.Players[0];
        Player bjørn = game.Players[1];
        Player catrin = game.Players[2];
        numCards -= 15; // 5 per spiller
        Assert.True(game.Deck.Count() == numCards);

        /* foreach (var item in albert.Hand) */
        /* { */
        /*     Console.WriteLine(item.Type); */
        /* } */
        /* foreach (var item in bjørn.Hand) */
        /* { */
        /*     Console.WriteLine(item.Type); */
        /* } */
        /* foreach (var item in catrin.Hand) */
        /* { */
        /*     Console.WriteLine(item.Type); */
        /* } */
        /* foreach (var item in game.Deck) */
        /* { */
        /*     Console.WriteLine(item.Type); */
        /* } */
        Assert.True(albert.StartingPlayer);
        Assert.True(game.CurrentPhase == Phase.Planting);
        var albertFields = albert.Fields.Keys.ToList();
        var bjørnFields = bjørn.Fields.Keys.ToList();
        var catrinFields = catrin.Fields.Keys.ToList();
        game.Plant(albertFields[0]);

        Assert.True(albert.Fields[albertFields[0]].First().Type == "GardenBean");
        game.EndPlanting();
        Assert.True(albert.DrawnCards.All(c => c.Type == "BlueBean"));
        Assert.True(bjørn.DrawnCards.Count() == 0);
        Assert.True(catrin.DrawnCards.Count() == 0);



        var trade1 = new Offer(albert.Id, albert.DrawnCards.Select(c=>c.Id).ToList(), new List<string>() { Card.SoyBean().Type });
        var trade2 = new Offer(albert.Id, albert.Hand.Where(c => c.Type == "RedBean").Union(albert.Hand.Where(c => c.Type == "StinkBean")).Select(s=>s.Id).ToList(), new List<string>() { Card.GardenBean().Type });

        game.AcceptTrade(catrin,trade1.OfferedCards, catrin.Hand.Where(c=> c.Type == "SoyBean").Select(s=>s.Id).ToList() );
        game.AcceptTrade(bjørn,trade2.OfferedCards, bjørn.Hand.Where(c=> c.Type == "GardenBean").Select(s=>s.Id).ToList());

        game.EndTrading();
        Assert.True(albert.Hand.Count() == 2);
        Assert.True(albert.DrawnCards.Count() == 0);
        Assert.True(albert.TradedCards.Where(c=>c.Type == "SoyBean").Count() == 1);
        Assert.True(albert.TradedCards.Where(c=>c.Type == "GardenBean").Count() == 1);
        Assert.True(albert.TradedCards.Count() == 2);

        Assert.True(bjørn.Hand.Count() == 4);
        Assert.True(bjørn.TradedCards.Where(c=>c.Type == "RedBean").Count() == 1);
        Assert.True(bjørn.TradedCards.Where(c=>c.Type == "StinkBean").Count() == 1);
        Assert.True(bjørn.TradedCards.Count() == 2);

        Assert.True(catrin.Hand.Count() == 4);
        Assert.True(catrin.TradedCards.Count() == 2);
        Assert.True(catrin.TradedCards.Where(c=>c.Type == "BlueBean").Count() == 2);
        game.PlantTrade(catrin,catrin.TradedCards.First(), catrinFields[1]);
        game.PlantTrade(catrin,catrin.TradedCards.First(), catrinFields[1]);
        Assert.True(catrin.TradedCards.Count() == 0);
        Assert.True(catrin.Fields[catrinFields[1]].Count() == 2);

        var bean = bjørn.TradedCards.First();
        game.PlantTrade(bjørn,bean, bjørnFields[0]);
        Assert.True(bjørn.Fields[bjørnFields[0]].First().Type == "StinkBean");

        bean = bjørn.TradedCards.First();
        game.PlantTrade(albert,albert.TradedCards.First(), albertFields[1]);
        game.PlantTrade(albert,albert.TradedCards.First(), albertFields[0]);
        Assert.True(albert.Fields[albertFields[0]].Count() == 2);
        Assert.True(albert.Fields[albertFields[0]].First().Type == "GardenBean");
        Assert.True(albert.Fields[albertFields[0]].Last().Type == "GardenBean");

        int cards = albert.Hand.Count();
        game.PlantTrade(bjørn,bjørn.TradedCards.First(), bjørnFields[1]);
        Assert.True(albert.Hand.Count() == cards + 3);
        Assert.True(bjørn.TradedCards.Count() == 0);
        Assert.True(game.CurrentPhase == Phase.Planting);
        Assert.True(game.CurrentPlayer == bjørn);

        game.Plant(bjørnFields[1]);
        game.Plant(bjørnFields[0]);

        var offer = new Offer(
                bjørn.Id,
                bjørn.DrawnCards.Where(c => c.Type == "SoyBean").ToList().Select(c=> c.Id).ToList(),
                new List<string> { "ChiliBean", "StinkBean" }
                );


        game.AcceptTrade(albert,offer.OfferedCards , 
                albert.Hand.Where(c => c.Type == "ChiliBean" || c.Type == "StinkBean").Select(s=> s.Id).ToList());

        game.EndTrading();
        Assert.True(bjørn.DrawnCards.Count() == 1);
        Assert.True(bjørn.TradedCards.Count() == 2);
        Assert.True(albert.TradedCards.Count() == 1);

        game.PlantTrade(bjørn,
                bjørn.TradedCards.Where(c=>
                    c.Type == "StinkBean")
                .First(), bjørnFields[0]);
        Assert.True(bjørn.Fields[bjørnFields[0]].Count() == 3);

        game.HarvestField(bjørn,bjørnFields[0]);
        Assert.True(bjørn.Fields[bjørnFields[0]].Count() == 0);
        Assert.True(bjørn.Coins == 1);
        Assert.True(game.Discard.Count() == 2);

        game.PlantTrade(bjørn,bjørn.TradedCards.First(), bjørnFields[0]);
        game.PlantTrade(bjørn,bjørn.DrawnCards.First(), bjørnFields[0]);
        game.PlantTrade(albert,albert.TradedCards.First(), albertFields[1]);
        Assert.True(bjørn.Hand.Count() == 5);
        Assert.True(game.CurrentPlayer == catrin);

        Assert.True(game.Deck.Count() + game.Discard.Count()+
                albert.Hand.Count() +
                bjørn.Hand.Count() +
                catrin.Hand.Count() +                    albert.Fields[albertFields[0]].Count() + albert.Fields[albertFields[1]].Count() +
                bjørn.Fields[bjørnFields[0]].Count() + bjørn.Fields[bjørnFields[1]].Count() +
                catrin.Fields[catrinFields[0]].Count() + catrin.Fields[catrinFields[1]].Count() == 103);
        game.Plant(catrinFields[1]);
        game.Plant(catrinFields[0]);
        game.EndTrading();
        game.PlantTrade(catrin, 
                catrin.DrawnCards.Where(c=>c.Type =="BlueBean").First(),catrinFields[1]);
        game.HarvestField(catrin,catrinFields[1]);
        foreach(var card in catrin.Hand)
        {
            Console.WriteLine(card.Type);
        }
        game.PlantTrade(catrin, 
                catrin.DrawnCards.Where(c=>c.Type =="BlackEyedBean").First(),catrinFields[1]);
        Assert.True(game.Deck.Count() + game.Discard.Count()+
                albert.Hand.Count() +
                bjørn.Hand.Count() +
                catrin.Hand.Count() +                    albert.Fields[albertFields[0]].Count() + albert.Fields[albertFields[1]].Count() +
                bjørn.Fields[bjørnFields[0]].Count() + bjørn.Fields[bjørnFields[1]].Count() +
                catrin.Fields[catrinFields[0]].Count() + catrin.Fields[catrinFields[1]].Count() == 102);
        //Nå er det alberts tur
    }
}
//p1 hand
/* GardenBean */
/* StinkBean */
/* RedBean */
/* SoyBean */
/* GreenBean */
//p2 hand
/* GardenBean */
/* RedBean */
/* StinkBean */
/* ChiliBean */
/* BlackEyedBean */
//p3 hand
/* BlueBean */
/* ChiliBean */
/* SoyBean */
/* ChiliBean */
/* BlackEyedBean */
//deck
/* BlueBean */
/* BlueBean */
/* StinkBean */
/* ChiliBean */
/* BlackEyedBean */
/* ChiliBean */
/* SoyBean */
/* GreenBean */
/* ChiliBean */
/* StinkBean */
/* BlueBean */
/* BlackEyedBean */
/* SoyBean */
/* BlueBean */
/* StinkBean */
/* BlackEyedBean */
/* GreenBean */
/* BlueBean */
/* RedBean */
/* SoyBean */
/* StinkBean */
/* SoyBean */
/* ChiliBean */
/* BlueBean */
/* BlackEyedBean */
/* GardenBean */
/* BlueBean */
/* BlueBean */
/* SoyBean */
/* GardenBean */
/* RedBean */

/* BlueBean */
/* RedBean */
/* BlueBean */
/* GardenBean */
/* ChiliBean */
/* StinkBean */
/* BlueBean */
/* GreenBean */
/* BlueBean */
/* BlueBean */
/* StinkBean */
/* ChiliBean */
/* StinkBean */
/* GreenBean */
/* BlueBean */
/* ChiliBean */
/* GreenBean */
/* BlackEyedBean */
/* GreenBean */
/* SoyBean */
/* GreenBean */
/* ChiliBean */
/* SoyBean */
/* GreenBean */
/* StinkBean */
/* ChiliBean */
/* ChiliBean */
/* BlueBean */
/* ChiliBean */
/* ChiliBean */
/* BlackEyedBean */
/* SoyBean */
/* StinkBean */
/* ChiliBean */
/* BlackEyedBean */
/* StinkBean */
/* SoyBean */
/* RedBean */
/* GreenBean */
/* ChiliBean */
/* GreenBean */
/* GreenBean */
/* BlueBean */
/* BlueBean */
/* RedBean */
/* StinkBean */
/* StinkBean */
/* GardenBean */
/* BlueBean */
/* GreenBean */
/* RedBean */
/* StinkBean */
/* StinkBean */
/* BlueBean */
/* ChiliBean */
/* BlackEyedBean */
/* GreenBean */
/* SoyBean */
