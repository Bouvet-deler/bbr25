using SharedModels;

namespace BoardGameServer.Application.Models;
public class GameStateDto
{
    public string CurrentPlayer { get; set; }
    public string CurrentPhase { get; set; }
    public string CurrentState { get; set; }
    public TimeSpan PhaseTimeLeft { get; set; }
    public int Deck { get; set; }
    public IEnumerable<TradeDto> AvailableTrades { get; set; }
    public Stack<Card> DiscardPile { get; set; }
    public IEnumerable<PlayerDto> Players { get; set; }
    public IEnumerable<HandCardDto> YourHand { get; set; }
}

public class TradeDto
{
    public Guid InitiatorId { get; set; }
    public List<string> OfferedCards { get; set; }
    public List<string> CardTypesWanted { get; set; }
}

public class PlayerDto
{
    public string Name { get; set; }
    public int Coins { get; set; }
    public IEnumerable<FieldDto> Fields { get; set; }
    public int Hand { get; set; }
    public IEnumerable<CardDto> DrawnCards { get; set; }
    public IEnumerable<CardDto> TradedCards { get; set; }
}

public class FieldDto
{
    public Guid Key { get; set; }
    public IEnumerable<CardDto> Card { get; set; }
}

public class CardDto
{
    public Guid Id { get; set; }
    public string Type { get; set; }
}

public class HandCardDto
{
    public bool FirstCard { get; set; }
    public Guid Id { get; set; }
    public string Type { get; set; }
}



