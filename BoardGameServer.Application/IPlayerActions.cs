using SharedModels;

namespace BoardGameServer.Application;

public interface IPlayerActions
{
    void Plant(Guid fieldId);
    void EndPlanting();

    void AcceptTrade(Player player,List<Guid> offeredCards, List<Guid> recievedCards);
    void EndTrading();
    void PlantTrade(Player player, Card card, Guid fieldId);
    Task<ResultOfferRequest> Negotiate(ResponseToOfferRequest request);
}
