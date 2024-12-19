namespace BoardGameServer.Application
{
    public interface IPlayerActions
    {
        void Plant(Guid fieldId);
        void EndPlanting();

        void OfferTrade(Offer trade);
        void AcceptTrade(Player player,Accept trade);
        void EndTrading();

        void PlantTrade(Player player, Card card, Guid fieldId);
    }
}
