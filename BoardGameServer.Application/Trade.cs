namespace BoardGameServer.Application
{
    public class Offer
    {
        public List<Card> OfferedCards;
        public List<String> Price;

        public Offer(List<Card> offeredCards, List<string> price){
            OfferedCards = offeredCards;
            Price = price;
        }
        public bool IsCompatible(Accept trade)
        {
            var equal = true;
            foreach(Card card in OfferedCards)
            {
                if (!trade.OfferedCards.Contains(card.Type))
                {
                    Console.WriteLine(card.Type);
                    equal = false;
                }
            }
            foreach(string type in trade.OfferedCards)
            {
                if (!OfferedCards.Select(c=> c.Type).Contains(type))
                {
                    Console.WriteLine("Typeoffered: " +type);
                    equal = false;
                }
            }
            foreach(Card card in trade.Price)
            {
                if (!Price.Contains(card.Type))
                {
                    Console.WriteLine("price" +card.Type);
                    equal = false;
                }
            }
            foreach(string type in Price)
            {
                if (!trade.Price.Select(c=> c.Type).Contains(type))
                {
                    Console.WriteLine("Typeprice: " +type);
                    equal = false;
                }
            }
            return equal;
        }
    }
    public class Accept
    {
        //Typen til bønnene du aksepterer
        public List<String> OfferedCards;
        public List<Card> Price;

        public Accept(List<string> offeredCards, List<Card> price){
            OfferedCards = offeredCards;
            Price = price;
        }
    }
}
