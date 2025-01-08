using Negotiator;
using SharedModels;
using Negotiator.Models;

namespace BoardGameServer.Application
{
    public class Game : IPlayerActions, IRegisterActions
    {

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

        //ToDo: Is this needed?
        public List<Offer> TradingArea;

        public INegotiationService NegotiationService { get; }

        public Game(INegotiationService negotiationService)
        {
            CurrentState = State.Registering;
            Players = new List<Player>();
            Discard = new Stack<Card>();
            Deck = new Stack<Card>();
            TradingArea = new List<Offer>();
            NegotiationService = negotiationService;
        }

        public Guid Join(string name)
        {
            var player = new Player(name);
            var firstPlayer = Players.FirstOrDefault();
            if (firstPlayer == null)
            {
                //Det er ingen andre spillere. Vi er vår egen neste
                player.NextPlayer = player;
            }
            else
            {
                //Den første spilleren i listen er den som skal spille etter oss
                player.NextPlayer = firstPlayer;
            }
            var lastPlayer = Players.LastOrDefault();
            //Er det ingen spillere, har vi håndtert spilleren vi setter inn nå i
            //forrige if
            if (lastPlayer != null)
            {
                //Siste spiller er ikke lenger siste.
                lastPlayer.NextPlayer = player;
            }
            Players.Add(player);

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
            for (int i = 0; i < 8; i++)
            {
                Discard.Push(Card.RedBean());
            }
            for (int i = 0; i < 18; i++)
            {
                Discard.Push(Card.ChiliBean());
            }
            for (int i = 0; i < 20; i++)
            {
                Discard.Push(Card.BlueBean());
            }
            for (int i = 0; i < 10; i++)
            {
                Discard.Push(Card.BlackEyedBean());
            }
            for (int i = 0; i < 16; i++)
            {
                Discard.Push(Card.StinkBean());
            }
            for (int i = 0; i < 12; i++)
            {
                Discard.Push(Card.SoyBean());
            }
            for (int i = 0; i < 14; i++)
            {
                Discard.Push(Card.GreenBean());
            }
            for (int i = 0; i < 6; i++)
            {
                Discard.Push(Card.GardenBean());
            }
            ShuffleDeck();
            //Deal hands

            foreach (var item in Players)
            {
                for (int i = 0; i < 5; i++)
                {
                    Card card = Deck.Pop();
                    item.Hand.Add(card);
                }

                for (int i = 0; i < 2; i++)
                {
                    item.Fields.Add(Guid.NewGuid(), new List<Card>());
                }
            }

            Players.FirstOrDefault().StartingPlayer = true;
            CurrentState = State.Playing;
            CurrentPhase = Phase.Planting;
            CurrentPlayer = Players.Single(p => p.StartingPlayer);
        }

        public void Plant(Guid field)
        {
            //Domene
            var card = CurrentPlayer.Hand[0];
            CurrentPlayer.Hand.RemoveAt(0);
            CurrentPlayer.Fields[field].Add(card);
            //Tilstand
            switch (CurrentPhase)
            {
                case Phase.Planting:
                    if (CurrentPlayer.Hand.Count() > 0)
                    {
                        CurrentPhase = Phase.PlantingOptional;
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

        public NegotiationState OfferTrade(NegotiationRequest negotiationRequest)
        {
            this.TradingArea.Add(new Offer( negotiationRequest.CardsToExchange, negotiationRequest.CardsToReceive, negotiationRequest.NegotiationId));
            var negotiationState = NegotiationService.StartNegotiation(negotiationRequest);
            var timer = new System.Timers.Timer(120000); // 2 minutes in milliseconds
            timer.Elapsed += (sender, e) => EndNegotiation(negotiationState);
            timer.AutoReset = false;
            timer.Start();
            return negotiationState;
        }


        public async Task<ResultOfferRequest> Negotiate(ResponseToOfferRequest request)
        {
            var response = await NegotiationService.RespondToNegotiationAsync(request);
            Player opponentPlayer = Players.Single(p => p.Id == request.ReceiverId);
            if (response.OfferStatus == OfferStatus.Accepted)
            {
                var result = AcceptTrade(opponentPlayer, request.NegotiationId, response.CardsExchanged, response.CardsReceived);
                //ToDo: Global variable?
                CurrentPlayer.Hand = result.CurrentPlayerHand;
                var oppontentHand = result.OpponentPlayerHand;
                return new ResultOfferRequest(CurrentPlayer.Id, opponentPlayer.Id, request.NegotiationId)
                {
                    CardsExchanged = response.CardsExchanged,
                    CardsReceived = response.CardsReceived,
                    OfferStatus = OfferStatus.Accepted
                };
            }
            else
            {
                return new ResultOfferRequest(CurrentPlayer.Id, request.ReceiverId, request.NegotiationId)
                {
                    OfferStatus = OfferStatus.Declined,
                    CardsExchanged = new List<Card>(),
                    CardsReceived = new List<Card>()
                };
            }
        }

        private void EndNegotiation(NegotiationState negotiationState)
        {
            NegotiationService.EndNegotiation(negotiationState);
            EndTrading(negotiationState);
        }

        public (List<Card> CurrentPlayerHand, List<Card> OpponentPlayerHand) AcceptTrade(Player opponentPlayer, Guid offerId, List<Card> cardsExchanged, List<Card> cardsReceived)
        {
            List<Card> currentPlayerHand = CurrentPlayer.Hand;
            List<Card> opponentPlayerHand = opponentPlayer.Hand;
            List<Card> cardsToRemoveFromCurrentPlayer = new List<Card>();

            foreach (var card in currentPlayerHand)
            {
                //Swaps cards from current player to opponent player
                if (cardsExchanged.Any(exchangedCard => exchangedCard.Id == card.Id))
                {
                    opponentPlayerHand.Add(card);
                    cardsToRemoveFromCurrentPlayer.Add(card);
                }
            }

            foreach (var card in cardsToRemoveFromCurrentPlayer)
            {
                currentPlayerHand.Remove(card);
            }

            List<Card> cardsToRemoveFromOpponentPlayer = new List<Card>();

            foreach (var cardHand in opponentPlayerHand)
            {
                // Remove cards received from opponent player and add to current player hand
                if (cardsReceived.Any(card => card.Id == cardHand.Id))
                {
                    currentPlayerHand.Add(cardHand);
                    cardsToRemoveFromOpponentPlayer.Add(cardHand);
                }
            }

            foreach (var cardHand in cardsToRemoveFromOpponentPlayer)
            {
                opponentPlayerHand.Remove(cardHand);
            }

            return (currentPlayerHand, opponentPlayerHand);
        }

        public void EndTrading(NegotiationState negotiationState)
        {
            TradingArea.Clear();
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
            if (!didRemove)
            {
                didRemove = player.DrawnCards.Remove(card);
                if (!didRemove)
                {
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

        }

        void GoToTradingPhase()
        {
            CurrentPhase = Phase.Trading;
            for (int i = 0; i < 2; i++)
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

            for (int i = 0; i < 3; i++)
            {
                var card = DrawCard();
                if (card != null)
                {
                    CurrentPlayer.Hand.Add(card);
                }
            }

            if (!GameEnded)
            {
                CurrentPlayer = CurrentPlayer.NextPlayer;
                if(CurrentPlayer.Hand.Any())
                {
                    CurrentPhase = Phase.Planting;
                }else{
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
            catch (InvalidOperationException e)
            {
                NumberOfDeckTurns++;
                if (NumberOfDeckTurns < 2)
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

        //Tar alt fra discard pilen, stokker om innholdet, og legger det i decken
        public void ShuffleDeck()
        {
            int discards = Discard.Count;
            Card[] list = new Card[discards];

            for (int i = 0; i < discards; i++)
            {
                list[i] = Discard.Pop();
            }
            random.Shuffle(list);

            for (int i = 0; i < discards; i++)
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
                player.Fields[field].RemoveAll(e => true);
            }
        }
        public void HandleGameEnd()
        {
            CurrentState = State.GameDone;
        }
    }
}

