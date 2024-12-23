
using SharedModels;

namespace BoardGameServerSimple.Services;

public class MessageValidator : IMessageValidator
{
    public bool Validate(NegotiationRequest negotiationRequest)
    {
        throw new NotImplementedException();
    }

    public bool Validate(ResponseRequest response)
    {
        throw new NotImplementedException();
    }
}
