using Negotiator.Models;
using SharedModels;
using System.Collections.Concurrent;

namespace Negotiator;

public class NegotiationService : INegotiationService
{
    private readonly ConcurrentDictionary<Guid, NegotiationState> _negotiations = new();
    private readonly SemaphoreSlim _semaphore = new(1, 1);


    public NegotiationState StartNegotiation(NegotiationRequest request)
    {
        var negotiation = new NegotiationState(
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

        _negotiations[negotiation.Id] = negotiation;

        return negotiation;
    }
    public NegotiationState? GetNegotiationStatus(Guid id)
    {
        return _negotiations.Values.FirstOrDefault(n => n.Id == id);
    }

    public async Task<ResultOfferRequest> RespondToNegotiationAsync(ResponseToOfferRequest request)
    {
        await _semaphore.WaitAsync();
        try
        {
            ResultOfferRequest endingOfferRequest = new ResultOfferRequest(request.InitiatorId, request.ReceiverId, request.NegotiationId);

            if (_negotiations.TryGetValue(request.NegotiationId, out var negotiation) && negotiation.IsActive)
            {
                if (negotiation.OfferAccepted)
                {
                    //Swap cards
                    endingOfferRequest.OfferStatus = OfferStatus.Accepted;
                    endingOfferRequest.CardsExchanged = negotiation.CardOffered;
                    endingOfferRequest.CardsReceived = negotiation.CardWanted;
                    return endingOfferRequest;
                }
                if (!negotiation.OfferAccepted)
                {
                    endingOfferRequest.OfferStatus = OfferStatus.Declined;
                    endingOfferRequest.CardsExchanged = negotiation.CardWanted;
                    endingOfferRequest.CardsReceived = negotiation.CardOffered;
                    return endingOfferRequest;
                }
            }
            endingOfferRequest.OfferStatus = OfferStatus.NotValid;
            endingOfferRequest.CardsExchanged = new List<Card>();
            endingOfferRequest.CardsReceived =  new List<Card>();
            return endingOfferRequest;
        }
        finally
        {
            _semaphore.Release();
        }
    }

    public void EndNegotiation(object? state)
    {
        if (state is NegotiationState negotiationState)
        {
            var negotiationId = negotiationState.Id;
            if (_negotiations.TryGetValue(negotiationId, out var negotiation))
            {
                negotiation.IsActive = false;
            }
        }
    }
}
