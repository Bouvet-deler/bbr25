using ScoringService;
using SharedModels;
using Negotiator.Models;
using BoardGameServer.Application.Models;

namespace BoardGameServer.Application;

public class Game : IPlayerActions, IRegisterActions
{
    public Lock Lock = new Lock();
    private NegotiationState _negotiationState;

    public List<Player> Players;
    public State CurrentState;

    // Er null om spillet ikke er i gang
    // Laget for å holde styr på hvor i runden vi er
    public Player CurrentPlayer;

    //Holder styr på hvor i turen vi er. 
    public Phase CurrentPhase;

    public int NumberOfDeckTurns;
    public bool GameEnded;
    public Stack<Card> Deck;
    public Stack<Card> Discard;
    public Random random = new Random();
    private readonly EloCalculator _eloCalculator;

    public readonly List<Offer> TradingArea;
    public DateTime LastStateChange = DateTime.Now; 

    public Game(EloCalculator eloCalculator)
    {
        CurrentState = State.Registering;
        Players = new List<Player>();
        Discard = new Stack<Card>();
        Deck = new Stack<Card>();
        TradingArea = new List<Offer>();

        _eloCalculator = eloCalculator;
    }

    //TODO registrer spillerene i eloRatingen
    public Guid Join(string name)
    {
        var player = new Player(name);
        Players.Add(player);
        if (!_eloCalculator.ScoreRepository.GetScores().Any(kv => kv.Key == name))
        {
            _eloCalculator.ScoreRepository.NewPlayer(name);
        }

        return player.Id;
    }

    public void StartGame()
    {
        if (Players == null || !Players.Any())
        {
            throw new InvalidOperationException("No players available to start the game.");
        }

        Discard = new Stack<Card>();
        //Legger ting i discard, så shuffles det, og da havner det i decken
        for(int i = 0; i < 8; i++)
        {
            Discard.Push(Card.RedBean());
        }
        for(int i = 0; i < 18; i++)
        {
            Discard.Push(Card.ChiliBean());
        }
        for(int i = 0; i < 20; i++)
        {
            Discard.Push(Card.BlueBean());
        }
        for(int i = 0; i < 10; i++)
        {
            Discard.Push(Card.BlackEyedBean());
        }
        for(int i = 0; i < 16; i++)
        {
            Discard.Push(Card.StinkBean());
        }
        for(int i = 0; i < 12; i++)
        {
            Discard.Push(Card.SoyBean());
        }
        for(int i = 0; i < 14; i++)
        {
            Discard.Push(Card.GreenBean());
        }
        for(int i = 0; i < 6; i++)
        {
            Discard.Push(Card.GardenBean());
        }
        ShuffleDeck();
        //Deal hands

        for (var playerNum = 0;playerNum<Players.Count(); playerNum++)
        {
            var item = Players[playerNum];
            if (playerNum == 0)
            {
                item.StartingPlayer = true;
            }
            try{
                item.NextPlayer = Players[playerNum+1];
            }
            catch(Exception e)
            {
                item.NextPlayer = Players[0];
            }
            item.PositionFromStarting = playerNum;

            for (int i = 0; i < 5; i++)
            {
                Card card = Deck.Pop();
                item.Hand.Enqueue(card);
            }

            for (int i = 0; i < 2; i++)
            {
                item.Fields.Add(Guid.NewGuid(), new List<Card>());
            }
        }
        CurrentState = State.Playing;
        CurrentPhase = Phase.Planting;
        CurrentPlayer = Players.Single(p=> p.StartingPlayer);
        LastStateChange = DateTime.Now;
    }

    public void Plant(Guid field)
    {
        //Domene
        var card = CurrentPlayer.Hand.Dequeue();
        CurrentPlayer.Fields[field].Add(card);
        //Tilstand
        switch (CurrentPhase)
        {
            case Phase.Planting:
                if (CurrentPlayer.Hand.Count() > 0)
                {
                    CurrentPhase = Phase.PlantingOptional;
                    LastStateChange = DateTime.Now;
                }
                else
                {
                    GoToTradingPhase();
                }
                break;
            case Phase.PlantingOptional:
                GoToTradingPhase();
                break;
            default:
                throw new Exception($"Valideringen er ikke fullstendig. {CurrentPhase} and {CurrentPlayer}");
        }

    }

    public void EndPlanting()
    {
        //Domene
        //Ingenting skjer i domene
        //Tilstand
        switch (CurrentPhase)
        {
            case Phase.Planting:
            case Phase.PlantingOptional:
                GoToTradingPhase();
                break;
            default:
                throw new Exception($"Valideringen er ikke fullstendig. {CurrentPhase} and {CurrentPlayer}");
        }
    }

    public void RequestTrade(Offer offer)
    {
        if(offer.CardTypesWanted == null)
        {
            offer.CardTypesWanted = new List<string>();
        }
        if(offer.OfferedCards == null)
        {
            offer.OfferedCards = new List<Card>();
        }
        if (!TradingArea.Any(already => already.InitiatorId == offer.InitiatorId && ListEquals(already.OfferedCards, offer.OfferedCards) && ListEquals(already.CardTypesWanted, offer.CardTypesWanted)))
        {
            TradingArea.Add(offer);
         }
    }
    private bool ListEquals<T>(IEnumerable<T> l1, IEnumerable<T> l2)
    {
        return l1.All(elem => l2.Contains(elem) && l2.All(elem => l1.Contains(elem)));
    }

    public void AcceptTrade(Player initiator,Player accepter, List<Guid> offeredCards, List<Guid> recievedCards)
    {
        //Finner det kompatible budet i trading acrea
        Queue<Card> currentPlayerHand = initiator.Hand;
        Queue<Card> currentPlayerNewHand = new Queue<Card>();

        foreach (var item in currentPlayerHand)
        {
            //Fjerner alle kort som ble byttet bort
            if (!offeredCards.Any(card =>card == item.Id))
            {
                currentPlayerNewHand.Enqueue(item);
            }
            else
            {
                accepter.TradedCards.Add(item);
            }
        }
        var drawnCards = CurrentPlayer.DrawnCards;
        var drawnCardsRemove = new List<Card>();
        foreach (var item in drawnCards)
        {
            //Fjerner alle kort som ble byttet bort
            if (offeredCards.Any(card => card == item.Id))
            {
                accepter.TradedCards.Add(item);
                drawnCardsRemove.Add(item);
            }
        }

        CurrentPlayer.DrawnCards.RemoveAll(c => drawnCardsRemove.Contains(c));

        CurrentPlayer.Hand = currentPlayerNewHand;
        Queue<Card> playerHand = accepter.Hand;
        Queue<Card> playerNewHand = new Queue<Card>();
        foreach (var item in playerHand)
        {
            //Fjerner alle kort som ble byttet bort
            if (!recievedCards.Any(card =>card == item.Id))
            {
                playerNewHand.Enqueue(item);
            }
            else
            {
                CurrentPlayer.TradedCards.Add(item);
            }
        }
        accepter.Hand = playerNewHand;

    }

    public void EndTrading()
    {
        //ToDo: This for NegotiationState object is needed for the timer. Can be removed if we don't use timer. 
        switch (CurrentPhase)
        {
            case Phase.Trading:
                GoToTradePlanting();
                break;
            default:
                throw new Exception($"Valideringen er ikke fullstendig. {CurrentPhase} and {CurrentPlayer}");
        }
    }  

    public void PlantTrade(Player player, Card card, Guid field)
    {
        bool didRemove = player.TradedCards.Remove(card);
        if (!didRemove) {
            didRemove = player.DrawnCards.Remove(card);
            if (!didRemove) {
                throw new Exception("Valider bedre!");
            }
        }
        player.Fields[field].Add(card);

        // if all players have planted their trades
        // 
        if (CurrentPlayer.DrawnCards.Count() == 0 &&
                Players.All(player => player.TradedCards.Count() == 0))
        {
            GoToPlantingPhase();
        }
        else
        {
        }
    }

    void GoToTradingPhase()
    {
        LastStateChange = DateTime.Now;
        CurrentPhase = Phase.Trading;
        for(int i = 0; i<2; i++)
        {
            var card = DrawCard();
            if (card != null)
            {
                CurrentPlayer.DrawnCards.Add(card);
            }
        }

    }

    public void GoToPlantingPhase()
    {
        
        LastStateChange = DateTime.Now;
        for(int i = 0; i<3; i++)
        {
            var card = DrawCard();
            if (card != null)
            {
                CurrentPlayer.Hand.Enqueue(card);
            }
        }

        if (!GameEnded)
        {
            CurrentPlayer = CurrentPlayer.NextPlayer;
            if(CurrentPlayer.Hand.Any())
            {
                CurrentPhase = Phase.Planting;
            }
            else
            {
                GoToTradingPhase();
            }
        }
        else
        {
            HandleGameEnd();
        }

    }

    public void GoToTradePlanting()
    {
        TradingArea.Clear();
        LastStateChange = DateTime.Now;
        CurrentPhase = Phase.TradePlanting;
    }

    //Trekker kort fra bunken og returnerer det
    //returnerer null om bunken er snudd for siste gang, og spillet er over
    public Card? DrawCard()
    {
        Card? card = null;
        try
        {
            card = Deck.Pop();
        }
        catch(InvalidOperationException e)
        {
            NumberOfDeckTurns++;
            if (NumberOfDeckTurns > 2)
            {
                GameEnded = true;
            }
            else
            {
                ShuffleDeck();
                card = Deck.Pop();
            }
        }
        return card;
    }

    // 
    public void CheckForTimeout()
    {
        if (CurrentState != State.Playing)
        {
            return;
        }
        var now = DateTime.Now;
        if((now - LastStateChange) < TimeSpan.FromMinutes(2))
        /* if((now - LastStateChange) < TimeSpan.FromSeconds(5)) */
        {
            // vi er innenfor makstid, fortsett som vanlig
            return ;
        }


        switch (CurrentPhase)
        {
            case Phase.Planting:
            case Phase.PlantingOptional:
                RemovePlayerFromGame(CurrentPlayer);
                CurrentPlayer = CurrentPlayer.NextPlayer;
                CurrentPhase = Phase.Planting;
                LastStateChange = DateTime.Now;
                break;

            case Phase.Trading:
                //Vi straffer ikke en spiller for å ikke ende trading på tiden
                //Kunne sikkert om vi vil være strenge
                GoToTradePlanting();
                break;
            case Phase.TradePlanting:
                //Remove all players who have cards that aren't planted
                var players = Players.Where(p=> p.TradedCards.Any() || p.DrawnCards.Any());
                
                foreach(Player player in players)
                {
                    RemovePlayerFromGame(player);
                }
                //Vi bruker ikke metoden for å gå til planting for da trekker feil
                //spiller kort
                CurrentPhase = Phase.Planting;
                CurrentPlayer = CurrentPlayer.NextPlayer;
                LastStateChange = DateTime.Now;
                break;
            default:
                break;

        }

    }

    /// <summary>
    /// Gjør slik at spilleren ikke lenger er i neste spiller rotasjonen (Det blir ikke
    /// denne spillerens tur igjen, 
    /// og kortene spilleren har, returneres til discard pilen
    /// </summary>
    /// <param name="player"></param>
    /// <returns></returns>
    public void RemovePlayerFromGame(Player player)
    {
        var forrigeSpiller = player;
        while(forrigeSpiller.NextPlayer != player)
        {
            forrigeSpiller = forrigeSpiller.NextPlayer;
        }

        //Her må vi gjøre noe om det bare er en spiller igjen
        forrigeSpiller.NextPlayer = player.NextPlayer;

        foreach(var field in player.Fields)
        {
            foreach(var card in field.Value)
            {
                Discard.Push(card);
            }
            field.Value.Clear();
        }
        foreach(var card in player.Hand)
        {
            Discard.Push(card);
        }
        player.Hand.Clear();

        foreach(var card in player.TradedCards)
        {
            Discard.Push(card);
        }
        player.TradedCards.Clear();
        foreach(var card in player.DrawnCards)
        {
            Discard.Push(card);
        }
        player.DrawnCards.Clear();

    }

    //Tar alt fra discard pilen, stokker om innholdet, og legger det i decken
    public void ShuffleDeck()
    {
        int discards = Discard.Count;
        Card[] list = new Card[discards];

        for(int i = 0; i < discards; i++)
        {
            list[i] = Discard.Pop();
        }
        random.Shuffle(list);

        for(int i = 0; i < discards; i++)
        {
            Deck.Push(list[i]);
        }
    }
//Etter denne er kallt, skal feltet være tømt, få penger utifra kortene de har
    //høstet, og om det er noen, skal kortene bli lagt i discard pilen
    public void HarvestField(Player player, Guid field)
    {
        int count = player.Fields[field].Count();   
        if (count == 0)
        {

            return; 
        }
        else
        {
            var card = player.Fields[field].First();
            int coins = card.Harvest(count);
            player.Coins += coins;
            for (int i = coins; i < player.Fields[field].Count(); i++)
            {
                Discard.Push(player.Fields[field][i]);
            }
            player.Fields[field].RemoveAll(e=> true);
        }
    }
    public void HandleGameEnd()
    {
        CurrentState = State.GameDone;
        var players = Players
            .OrderByDescending(p=> p.Coins)
            .ThenByDescending(p=>p.PositionFromStarting)
            .Select(p=> p.Name)
            .ToList<string>();

        _eloCalculator.ScoreGame(players);
    }

    public static GameStateDto CreateGameState(Game game, Queue<Card> hand)
    {
        return new GameStateDto
        {
            CurrentPlayer = game.CurrentPlayer == null ? "" : game.CurrentPlayer.Name,
            CurrentPhase = PhaseUtil.GetDescription(game.CurrentPhase),
            CurrentState = StateUtil.GetDescription(game.CurrentState),
            Round = game.NumberOfDeckTurns + 1,
            PhaseTimeLeft = game.LastStateChange.AddMinutes(2) - DateTime.Now,

            Deck = game.Deck.Count(),
            AvailableTrades = game.TradingArea.Select(negotiaton => new TradeDto
            {
                InitiatorId = negotiaton.InitiatorId,
                OfferedCards = negotiaton.OfferedCards.Select(s => s.Type).ToList(),
                CardTypesWanted = negotiaton.CardTypesWanted
            }),
            DiscardPile = game.Discard,
            Players = game.Players
        ?.Select(p => new PlayerDto
        {
            Name = p.Name,
            Coins = p.Coins,
            Fields = p.Fields.Select(kv => new FieldDto { Key = kv.Key, Card = kv.Value.Select(c => new CardDto { Id = c.Id, Type = c.Type, ExchangeMap = c.ExchangeMap.Select(em => new ExchangeMapEntry { CropSize = em.Item1, Value = em.Item2 }).ToList() }) }),
            Hand = p.Hand.Count(),
            DrawnCards = p.DrawnCards.Select(c => new CardDto { Id = c.Id, Type = c.Type, ExchangeMap = c.ExchangeMap.Select(em => new ExchangeMapEntry { CropSize = em.Item1, Value = em.Item2 }).ToList() }),
            TradedCards = p.TradedCards.Select(c => new CardDto { Id = c.Id, Type = c.Type })
        })?.ToList(),
            YourHand = hand.Select(c => new HandCardDto
            {
                FirstCard = hand.Peek() == c, //Bare for å gjøre det ekstra tydlig hvilket kort de kan spille
                Id = c.Id,
                Type = c.Type,
                ExchangeMap = c.ExchangeMap.Select(em => new ExchangeMapEntry { CropSize = em.Item1, Value = em.Item2 }).ToList(),
            }),
        };
    }
}

