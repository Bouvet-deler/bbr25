using SharedModels;

namespace NegotiatorService.Models;

public class NegotiationState(string initiator, string id, SimpleCard cardOffered, SimpleCard cardWanted)
{
    public string Id { get; init; } = id;
    public string Initiator { get; init; } = initiator;
    public string? Acceptor { get; set; }
    public SimpleCard CardOffered { get; init; } = cardOffered;
    public SimpleCard CardWanted { get; init; } = cardWanted;
    public bool OfferAccepted { get; set; } = false;
    public DateTime StartTime { get; init; } = DateTime.UtcNow;
    public bool IsActive { get; set; } = true;
}
