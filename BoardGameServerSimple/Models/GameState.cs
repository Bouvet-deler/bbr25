namespace BoardGameServerSimple.Models;

public class GameState
{
    private int _deckPlayed;
    public int DeckPlayed => _deckPlayed;

    public Player? CurrentPlayer { get; set; }
    public List<Player>? Players { get; set; }
    public IReadOnlyList<Card> Deck { get; }
    public List<Card> DiscardPile { get; set; }
    public Player? NextPlayer
    {
        get
        {
            if (Players is null or { Count: 0 or 1 } || CurrentPlayer is null)
            {
                return null;
            }

            int currentIndex = Players.IndexOf(CurrentPlayer);
            int nextIndex = (currentIndex + 1) % Players.Count;
            return Players[nextIndex];
        }
    }


    public GameState(List<Card> initialDeck)
    {
        Deck = new List<Card>(initialDeck);
        DiscardPile = new List<Card>();
        _deckPlayed = 0;
    }

    public Card? DrawCard()
    {
        if (Deck.Count == 0)
        {
            _deckPlayed++;
            return null;
        }

        var card = Deck[0];
        ((List<Card>)Deck).RemoveAt(0);
        return card;
    }

    public List<Card> ShuffleDeck()
    {
        var random = new Random();
        var shuffledDeck = new List<Card>(Deck);
        for (int i = shuffledDeck.Count - 1; i > 0; i--)
        {
            int j = random.Next(0, i + 1);
            var temp = shuffledDeck[i];
            shuffledDeck[i] = shuffledDeck[j];
            shuffledDeck[j] = temp;
        }
        return shuffledDeck;
    }
}
