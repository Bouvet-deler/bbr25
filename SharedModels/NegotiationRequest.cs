namespace SharedModels;

public record NegotiationRequest(Guid InitiatorId, Guid ReceiverId, Guid NegotiationId, List<Card> CardsToExchange, List<Card> CardsToReceive);
