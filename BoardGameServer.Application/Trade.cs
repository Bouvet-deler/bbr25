namespace BoardGameServer.Application
{
    public class Offer
    {
        public List<Card> OfferedCards;
        public List<String> Price;
        public Guid Id;

        public Offer(List<Card> offeredCards, List<string> price){
            OfferedCards = offeredCards;
            Price = price;
            Id = Guid.NewGuid();
        }
    }
}
