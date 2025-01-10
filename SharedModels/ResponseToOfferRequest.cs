namespace SharedModels;

public record ResponseToOfferRequest(Guid InitiatorId, Guid ReceiverId, Guid NegotiationId, ProposalStatus answer);
