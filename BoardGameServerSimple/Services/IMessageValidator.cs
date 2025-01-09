using SharedModels;

namespace BoardGameServerSimple.Services;

public interface IMessageValidator
{
    bool Validate(ResponseToOfferRequest response);
    bool Validate(NegotiationRequest negotiationRequest);
}
