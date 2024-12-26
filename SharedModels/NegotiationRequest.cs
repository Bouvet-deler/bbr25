namespace SharedModels;

public record NegotiationRequest(Guid PlayerId, Guid NegotiationId, List<Card> CardsToExchange, List<Card> CardsToReceive);
