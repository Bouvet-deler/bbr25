namespace BoardGameServerSimple.Models;

public class Card
{
    public CardType CardType { get; }
    public (Dictionary<string, int>, Dictionary<string, int>) Beanometer { get; }
    public int Quantity { get; set; }

    public Card(CardType cardType, int beanometer1, int beanometer2, int quantity)
    {
        if (beanometer1 <= 0 || beanometer2 <= 0)
        {
            throw new ArgumentException("Beanometer values must be positive integers.");
        }

        CardType = cardType;
        Beanometer = (new Dictionary<string, int> { { "amount", beanometer1 } }, new Dictionary<string, int> { { "score", beanometer2 } });
        Quantity = quantity;
    }
}
