using Negotiator.Models;
using SharedModels;
using System.Collections.Concurrent;

namespace Negotiator
{
    public interface INegotiationService
    {
        NegotiationState StartNegotiation(Offer request);
        (NegotiationState? negotiationState, ConcurrentDictionary<Guid, Offer> negotiations) GetNegotiationStatus();
        string RegisterOffer(Offer offer);
        ResultOfferRequest RespondToNegotiation(ResponseToOfferRequest response);
        void EndNegotiation(object? state);
    }
}