namespace SharedModels;

public record NegotiationRequest(string PlayerId, SimpleCard CardsToExchange, SimpleCard CardsToReceive);
