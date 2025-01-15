using BoardGameServer.Application.Models;
using SharedModels;

namespace BoardGameServer.Application;

public interface IPlayerActions
{
    void Plant(Guid fieldId);
    void EndPlanting();

    void RequestTrade(Offer offer);
    void AcceptTrade(Player player,List<Guid> offeredCards, List<Guid> recievedCards);
    void EndTrading();
    void PlantTrade(Player player, Card card, Guid fieldId);
}
