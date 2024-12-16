using BoardGameServerSimple.Models;

namespace BoardGameServerSimple.Services;

public class CardValidator
{
    internal bool Validate(Card card)
    {
        // Validate the card according to game rules
        //Player has the card in his hand
        //The card is drawn from the correct position from the players hand. (In the order it was drawn)
        return true;
    }
}
