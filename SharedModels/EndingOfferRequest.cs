namespace SharedModels;

public record EndingOfferRequest
{
    public Guid PlayerId { get; }
    public Guid NegotiationId { get; }
    public OfferStatus OfferStatus { get; set; }
    public List<Card> CardsExchanged { get; set; }
    public List<Card> CardsReceived { get; set; }

    public EndingOfferRequest(Guid playerId, Guid negotiationId)
    {
        PlayerId = playerId;
        NegotiationId = negotiationId;
    }
}


 

