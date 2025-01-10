namespace SharedModels;

public record ResultOfferRequest
{
    public Guid InitiatorId { get; }
    public Guid ReceiverId { get; }
    public Guid NegotiationId { get; }
    public OfferStatus OfferStatus { get; set; }
    public List<Card> CardsGiven { get; set; } = [];
    public ProposalStatus OfferStatus { get; set; }
    public List<Card> CardsExchanged { get; set; } = [];
    public List<Card> CardsReceived { get; set; } = [];

    public ResultOfferRequest(Guid initiatorId, Guid receiverId, Guid negotiationId)
    {
        InitiatorId = initiatorId;
        ReceiverId = receiverId;
        NegotiationId = negotiationId;
    }
}