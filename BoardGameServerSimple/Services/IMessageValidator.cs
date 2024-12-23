using SharedModels;

namespace BoardGameServerSimple.Services
{
    public interface IMessageValidator
    {
        bool Validate(ResponseRequest response);
        bool Validate(NegotiationRequest negotiationRequest);
    }
}
