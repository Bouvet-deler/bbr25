using Negotiator.Models;
using SharedModels;
using System.Collections.Concurrent;

namespace Negotiator;

public class NegotiationService : INegotiationService  //ToDo: update interface
{
    public ConcurrentDictionary<Guid, NegotiationState> Negotiations  {get; } = new();
    private readonly SemaphoreSlim _semaphore = new(1, 1);

    //ToDo: This will not work in a real-world scenario. This is just for testing purposes.
    //Need to support multiple negotiations at the same time.
    private Guid _negotiationId = Guid.NewGuid();

    public event EventHandler<NegotiationState>? OnNegotiationCompleted;
    //public delegate void NegotiationCompletedCallback(NegotiationState state);
    //public event NegotiationCompletedCallback? OnNegotiationCompleted;


    


    public NegotiationState StartNegotiation(NegotiationRequest request)
    {
        var negotiation = new NegotiationState(
            request.InitiatorId,
            request.ReceiverId,
            _negotiationId,
            request.OfferedCards,
            request.CardTypesWanted
        )
        {
            StartTime = DateTime.UtcNow,
            IsActive = true
        };

        Negotiations[negotiation.Id] = negotiation;

        return negotiation;
    }
    public NegotiationState? GetNegotiationStatus(Guid id)
    {
        return Negotiations.Values.FirstOrDefault(n => n.Id == id);
    }

    public async Task<ResultOfferRequest> RespondToNegotiationAsync(ResponseToOfferRequest request)
    {
        await _semaphore.WaitAsync();
        try
        {
            //ToDo: Use _negotiationId
            ResultOfferRequest endingOfferRequest = new ResultOfferRequest(request.InitiatorId, request.ReceiverId, request.NegotiationId);

            if (Negotiations.TryGetValue(request.NegotiationId, out var negotiation) && negotiation.IsActive)
            {
                if (negotiation.OfferAccepted)
                {
                    //Swap cards
                    endingOfferRequest.OfferStatus = OfferStatus.Accepted;
                    endingOfferRequest.CardsGiven = negotiation.CardOffered;
                    //ToDO: Need to swap real cards, not only type
                    //endingOfferRequest.CardsReceived = negotiation.CardWanted;

                    OnNegotiationCompleted?.Invoke(this, negotiation);

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
            endingOfferRequest.CardsGiven = new List<Card>();
            endingOfferRequest.CardsReceived = new List<Card>();
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
            if (Negotiations.TryGetValue(negotiationId, out var negotiation))
            {
                negotiation.IsActive = false;
            }
        }
    }
}
