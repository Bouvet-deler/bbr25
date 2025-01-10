using Negotiator.Models;
using SharedModels;
using System.Collections.Concurrent;
using System.Threading.Tasks;

namespace Negotiator;

public interface INegotiationService
{
    public  ConcurrentDictionary<Guid, NegotiationState> Negotiations  {get;}
    event EventHandler<NegotiationState>? OnNegotiationCompleted;
    NegotiationState StartNegotiation(NegotiationRequest request);
    NegotiationState? GetNegotiationStatus(Guid id);
    Task<ResultOfferRequest> RespondToNegotiationAsync(ResponseToOfferRequest request);
    void EndNegotiation(object? state);
}