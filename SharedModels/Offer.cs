namespace SharedModels;

public record Offer(Guid InitiatorId, Guid ReceiverId, Guid NegotiationId, List<Card> OfferedCards, List<string> CardTypesWanted);
