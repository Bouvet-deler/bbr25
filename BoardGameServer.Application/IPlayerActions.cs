using SharedModels;

namespace BoardGameServer.Application;

public interface IPlayerActions
{
    void Plant(Guid fieldId);
    void EndPlanting();

    void OfferTrade(NegotiationRequest request);
    void AcceptTrade(Player player,Guid offerId, List<Guid> payment);
    void EndTrading();
    void PlantTrade(Player player, Card card, Guid fieldId);
    Task<ResultOfferRequest> Negotiate(ResponseToOfferRequest request);
}
