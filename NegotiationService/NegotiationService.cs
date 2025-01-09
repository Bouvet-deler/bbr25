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
            request.OfferedCards,
            request.CardTypesWanted
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
                    endingOfferRequest.CardsOffered = negotiation.CardOffered;
                    //ToDO: Need to swap real cards, not only type
                    //endingOfferRequest.CardsReceived = negotiation.CardWanted;
                    return endingOfferRequest;
                }
                if (!negotiation.OfferAccepted)
                {
                    endingOfferRequest.OfferStatus = OfferStatus.Declined;
                    //ToDO: Need to swap real cards, not only type
                    //endingOfferRequest.CardsExchanged = negotiation.CardWanted;
                    endingOfferRequest.CardsReceived = negotiation.CardOffered;
                    return endingOfferRequest;
                }
            }
            endingOfferRequest.OfferStatus = OfferStatus.NotValid;
            endingOfferRequest.CardsOffered = new List<Card>();
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
