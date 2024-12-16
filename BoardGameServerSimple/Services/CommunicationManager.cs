
namespace BoardGameServerSimple.Services;

public class CommunicationManager
{
    internal string ReceiveMessages()
    {
        //Web hook
        return "I would like the swap this card";  //We need a standard for format for possible actions in negotiation. Enums.
    }

    internal Task SendMessage(string message)
    {
        throw new NotImplementedException();
    }
}
