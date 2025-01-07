using SharedModels;

namespace Negotiator.Models;

public class NegotiationState(Guid InitiatorId, Guid ReceiverId, Guid NegotiationId, List<Card> cardOffered, List<Card> cardWanted)
{
    public Guid Id { get; init; } = NegotiationId;
    public Guid Initiator { get; init; } = InitiatorId;
    public Guid Receiver { get; init; } = ReceiverId;
    public List<Card> CardOffered { get; set; } = cardOffered;      
    public List<Card> CardWanted { get; set; } = cardWanted;
    public bool OfferAccepted { get; set; } = false;
    public DateTime StartTime { get; init; } = DateTime.UtcNow;
    public bool IsActive { get; set; } = true;
}