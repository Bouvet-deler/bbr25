namespace BoardGameServerSimple.Models;

public class Player
{
    public string Name { get; }
    public Guid Key { get; }
    public List<Card> Hand { get; set; } = [];
    public List<Card>? CardsOnTable { get; set; } = [];
    public List<Card> CardsinField { get; set; } = [];
    public int Score { get; set; }

    public Player(string name, Guid key)
    {
        Name = name;
        Key = key;
    }
}
