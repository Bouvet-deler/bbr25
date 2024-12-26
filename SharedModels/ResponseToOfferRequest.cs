namespace SharedModels;

public record ResponseToOfferRequest(Guid PlayerId, Guid NegotiationId, bool answer);
