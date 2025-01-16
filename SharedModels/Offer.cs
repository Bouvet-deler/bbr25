namespace SharedModels;

public record Offer
{
    public Guid InitiatorId {get;set;}
    public Guid InitiatorName {get;set;}
    /* public Guid ReceiverId; */
    public Guid NegotiationId = Guid.NewGuid();
    public List<Card> OfferedCards{get;set;}
    public List<string> CardTypesWanted{get;set;}

    public Offer()
    {
    }
    public Offer(Guid initiatorId, List<Card> offeredCards, List<string> cardTypesWanted)
    {
        InitiatorId = initiatorId;
        OfferedCards = offeredCards;
        CardTypesWanted = cardTypesWanted;
    }
}
public record OfferDto
{
    public List<Guid> OfferedCards{get;set;}
    public List<string> CardTypesWanted{get;set;}
}

public record Accept
{
    public Guid NegotiationId{get;set;}
    public List<Guid> Payment{get;set;}

    public Accept()
    {
    }
    public Accept(Guid initiatorId, Guid receiverId, Guid negotiationId, List<Guid> payment)
    {
        NegotiationId = negotiationId;
        Payment = payment;
    }
}
