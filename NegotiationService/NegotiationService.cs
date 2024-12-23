using NegotiatorService.Models;
using SharedModels;
using System.Collections.Concurrent;

namespace NegotiatorService;

public class NegotiationService: INegotiationService
{
    private readonly ConcurrentDictionary<string, NegotiationState> _negotiations = new();
    private readonly SemaphoreSlim _semaphore = new(1, 1);


    public NegotiationState StartNegotiation(NegotiationRequest request)
    {
        var negotiation = new NegotiationState(
            request.PlayerId,
            Guid.NewGuid().ToString(),
            request.CardsToExchange,
            request.CardsToReceive
        )
        {
            StartTime = DateTime.UtcNow,
            IsActive = true
        };

        _negotiations[negotiation.Id] = negotiation;

        // Start a timer to end the negotiation after 5 seconds - 120 for debugging
        var timer = new Timer(EndNegotiation, negotiation, TimeSpan.FromSeconds(120), Timeout.InfiniteTimeSpan);

        return negotiation;
    }
    public NegotiationState? GetNegotiationStatus(Guid id)
    {
        return _negotiations.Values.FirstOrDefault(n => n.Id == id.ToString());
    }

    public async Task<string> RespondToNegotiationAsync(ResponseRequest request)
    {
        //Do we need _semaphore or not??
        await _semaphore.WaitAsync();
        try
        {
            if (_negotiations.TryGetValue(request.NegotiationId, out var negotiation) && negotiation.IsActive)
            {
                negotiation.IsActive = false;
                //Return someting else
                return $"Player {request.PlayerId} accepted the negotiation.";
            }
            return "Negotiation not found or already completed.";
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
