using BoardGameServerSimple.Models;

namespace BoardGameServerSimple.Services;

public class GameStateFactory
{
    public GameState CreateNewGameState()
    {
        var players = new List<Player>
        {
            CreateNewPlayer("Player 1"),
            CreateNewPlayer("Player 2"),
        };

        return new GameState(CreateDeck(10))
        {
            DiscardPile = new List<Card>(),
            Players = players,
            CurrentPlayer = players.First()
            
        };
    }

    private Player CreateNewPlayer(string name)
    {
        return new Player(name, Guid.NewGuid());
    }

    private List<Card> CreateDeck(int numberOfCards)
    {
        //Just for testing purposes.
        //In a real game, you would have a fixed deck of cards based on the number of cards for each card type => Card.Quantity
        var deck = new List<Card>();
        var random = new Random();
        var cardTypes = Enum.GetValues(typeof(CardType)).Cast<CardType>().ToList();

        for (int i = 0; i < numberOfCards; i++)
        {
            var cardType = cardTypes[random.Next(cardTypes.Count)];
            var beanometer1 = random.Next(1, 5);
            var beanometer2 = random.Next(1, 5);
            var quantity = random.Next(1, 10);
            deck.Add(new Card(cardType, beanometer1, beanometer2, quantity));
        }
        return deck;
    }
}
