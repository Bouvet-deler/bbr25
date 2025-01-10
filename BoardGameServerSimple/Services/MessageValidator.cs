
using SharedModels;

namespace BoardGameServerSimple.Services;

public class MessageValidator : IMessageValidator
{
    public bool Validate(Offer negotiationRequest)
    {
        throw new NotImplementedException();
    }

    public bool Validate(ResponseToOfferRequest response)
    {
        throw new NotImplementedException();
    }
}
