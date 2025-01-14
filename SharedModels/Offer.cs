﻿namespace SharedModels;

public record Offer
{
    public Guid InitiatorId {get;set;}
    /* public Guid ReceiverId; */
    public Guid NegotiationId = Guid.NewGuid();
    public List<Guid> OfferedCards{get;set;}
    public List<string> CardTypesWanted{get;set;}

    public Offer(){}
    public Offer(Guid initiatorId, List<Guid> offeredCards, List<string> cardTypesWanted)
    {
        InitiatorId = initiatorId;
        OfferedCards = offeredCards;
        CardTypesWanted = cardTypesWanted;
    }
}

public record Accept
{
    public Guid InitiatorId;
    public Guid ReceiverId;
    public Guid NegotiationId;
    public List<Guid> Payment;

    public Accept(Guid initiatorId, Guid receiverId, Guid negotiationId, List<Guid> payment)
    {
        InitiatorId = initiatorId;
        ReceiverId = receiverId;
        NegotiationId = negotiationId;
        Payment = payment;
    }
}
