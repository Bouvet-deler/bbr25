using SharedModels;

namespace BoardGameServer.Application;

public class Offer
{
    public List<Card> OfferedCards;
    public List<string> Price;  
    public Guid Id;

    public Offer(List<Card> offeredCards, List<string> price, Guid NegotiationId)
    {
        OfferedCards = offeredCards;
        Price = price;
        Id = NegotiationId;
    }
}
