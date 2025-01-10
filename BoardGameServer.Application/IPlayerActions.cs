using Negotiator.Models;
using SharedModels;

namespace BoardGameServer.Application
{
    public interface IPlayerActions
    {
        void Plant(Guid field);
        void EndPlanting();
        NegotiationState OfferTrade(SharedModels.Offer negotiationRequest);
        (List<Card> CurrentPlayerHand, List<Card> OpponentPlayerHand) AcceptTrade(Player opponentPlayer, Guid offerId, List<Card> cardsExchanged, List<Card> cardsReceived);
        void EndTrading(Guid negotiationId);
        void PlantTrade(Player player, Card card, Guid field);
    }
}
