using Negotiator.Models;
using SharedModels;

namespace BoardGameServer.Application
{
    public interface IPlayerActions
    {
        void Plant(Guid field);
        void EndPlanting();
        NegotiationState StartTrade(NegotiationRequest negotiationRequest);
        void AcceptTrade(Player player, Guid offerId, List<Guid> trade);
        void EndTrading(NegotiationState negotiationState);
        void PlantTrade(Player player, Card card, Guid field);
    }
}
