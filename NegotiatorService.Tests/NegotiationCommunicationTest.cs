using SharedModels;

namespace Negotiator.Tests;

public class NegotiationServiceTests
{
    private readonly NegotiationService _negotiationService;
    private readonly NegotiationRequest _request;

    public NegotiationServiceTests()
    {
        _negotiationService = new NegotiationService();
        _request = new NegotiationRequest(
            InitiatorId:Guid.NewGuid(),   
            ReceiverId:new Guid(),
            NegotiationId : Guid.NewGuid(),
            OfferedCards: new List<Card> { Card.BlackEyedBean()},
            CardTypesWanted: new List<string> { Card.ChiliBean().Type }
        );
    }

    [Fact]
    public void StartNegotiation_ShouldCreateNewNegotiation()
    {
        // Act
        var result = _negotiationService.StartNegotiation(_request);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(_request.InitiatorId, result.Initiator);
        Assert.Equal(_request.ReceiverId, result.Receiver);
        Assert.Equal(_request.OfferedCards, result.CardOffered);
        Assert.Equal(_request.CardTypesWanted, result.CardWanted);
        Assert.True(result.IsActive);
    }

    [Fact]
    public void GetNegotiationStatus_ShouldReturnCorrectNegotiation()
    {
        // Arrange
        var negotiation = _negotiationService.StartNegotiation(_request);

        // Act
        var result = _negotiationService.GetNegotiationStatus(negotiation.Id);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(negotiation.Id, result.Id);
    }

    [Fact]
    public async Task RespondToNegotiationAsync_ShouldReturnAcceptedOffer()
    {
        // Arrange
        var negotiation = _negotiationService.StartNegotiation(_request);
        negotiation.OfferAccepted = true;

        var responseRequest = new ResponseToOfferRequest(
            _request.InitiatorId,
            _request.ReceiverId,
            negotiation.Id, // NegotiationId
            true // OfferAccepted
        );

        // Act
        var result = await _negotiationService.RespondToNegotiationAsync(responseRequest);

        // Assert
        Assert.Equal(OfferStatus.Accepted, result.OfferStatus);
        Assert.Equal(negotiation.CardOffered, result.CardsGiven);
        //ToDo: Need to check for real cards, not only type
        //Assert.Equal(negotiation.CardWanted, result.CardsReceived);
    }

    [Fact]
    public async Task RespondToNegotiationAsync_ShouldReturnDeclinedOffer()
    {
        // Arrange
        var negotiation = _negotiationService.StartNegotiation(_request);
        negotiation.OfferAccepted = false;

        var responseRequest = new ResponseToOfferRequest(
            _request.InitiatorId,
            _request.ReceiverId,
            negotiation.Id, // NegotiationId
            false // OfferAccepted
        );

        // Act
        var result = await _negotiationService.RespondToNegotiationAsync(responseRequest);

        // Assert
        Assert.Equal(OfferStatus.Declined, result.OfferStatus);
        //ToDo: Need to check for real cards, not only type
        //Assert.Equal(negotiation.CardWanted, result.CardsOffered);
        Assert.Equal(negotiation.CardOffered, result.CardsReceived);
    }

    [Fact]
    public void EndNegotiation_ShouldSetNegotiationToInactive()
    {
        // Arrange
        var negotiation = _negotiationService.StartNegotiation(_request);

        // Act
        _negotiationService.EndNegotiation(negotiation);

        // Assert
        Assert.False(negotiation.IsActive);
    }
}
