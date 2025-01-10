using Negotiator.Models;
using SharedModels;
using System.Collections.Concurrent;
using System.ComponentModel;

namespace Negotiator;

public class NegotiationService : INegotiationService
{
    private readonly ConcurrentDictionary<Guid, Offer> _negotiations = new();
    private NegotiationState? _negotiationState;


    public NegotiationState StartNegotiation(Offer request)
    {
        _negotiationState = new NegotiationState(
            request.InitiatorId,
            request.ReceiverId,
            Guid.NewGuid(),
            request.CardsToExchange,
            request.CardsToReceive
        )
        {
            StartTime = DateTime.UtcNow,
            IsActive = true
        };

        return _negotiationState;
    }

    public (NegotiationState? negotiationState, ConcurrentDictionary<Guid, Offer> negotiations) GetNegotiationStatus()
    {
        //Can be used by both parties to check the status of the negotiation
        return (_negotiationState, _negotiations);  //ToDo: Refactor to return a DTO
    }

    public string RegisterOffer(Offer offer)
    {
        if (offer == null)
        {
            return "Error: Offer is null";
        }

        _negotiations.AddOrUpdate(
            offer.NegotiationId,
            offer,
            (key, existingOffer) => offer
        );

        return "OK";
    }

    public ResultOfferRequest RespondToNegotiation(ResponseToOfferRequest response)
    {
        if (_negotiationState == null || _negotiationState.Id != response.NegotiationId || !_negotiationState.IsActive)
        {
            if (response.answer == ProposalStatus.Accepted)
            {
                return new ResultOfferRequest(response.InitiatorId, response.ReceiverId, response.NegotiationId)
                {
                    OfferStatus = ProposalStatus.NotValid,
                    CardsExchanged = new List<Card>(),
                    CardsReceived = new List<Card>()
                };
            }
            return new ResultOfferRequest(response.InitiatorId, response.ReceiverId, response.NegotiationId)
            {
                OfferStatus = ProposalStatus.Declined,
                CardsExchanged = new List<Card>(),
                CardsReceived = new List<Card>()
            };
        }

        //No active negotiations running
        return new ResultOfferRequest(response.InitiatorId, response.ReceiverId, response.NegotiationId)
        {
            OfferStatus = ProposalStatus.NotValid,
            CardsExchanged = new List<Card>(),
            CardsReceived = new List<Card>()
        };
    }

    public void EndNegotiation(object? state)
    {
        if (state is NegotiationState negotiationState)
        {
            negotiationState.IsActive = false;  //???
            _negotiationState = null;
            _negotiations.Clear();
        }

        //ToDO: Do we need to do return the new state?
    }
}
