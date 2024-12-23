using NegotiatorService.Models;
using SharedModels;
using System.Threading.Tasks;

namespace NegotiatorService
{
    public interface INegotiationService
    {
        NegotiationState StartNegotiation(NegotiationRequest request);
        NegotiationState? GetNegotiationStatus(Guid id);
        Task<string> RespondToNegotiationAsync(ResponseRequest request);
        void EndNegotiation(object? state);
    }
}