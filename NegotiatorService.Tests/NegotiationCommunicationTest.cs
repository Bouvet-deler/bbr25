using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Moq;
using Xunit;
using Negotiator;
using SharedModels;

namespace Negotiator.Tests
{
    public class NegotiationServiceTests
    {
        private readonly NegotiationService _negotiationService;

        public NegotiationServiceTests()
        {
            _negotiationService = new NegotiationService();
        }

        [Fact]
        public void StartNegotiation_ShouldCreateNewNegotiation()
        {
            // Arrange
            var request = new NegotiationRequest(
                Guid.NewGuid(), // PlayerId
                Guid.NewGuid(), // NegotiationId
                new List<Card> { Card.BlackEyedBean() }, // CardsToExchange
                new List<Card> { Card.ChiliBean() } // CardsToReceive
            );

            // Act
            var result = _negotiationService.StartNegotiation(request);

            // Assert
            Assert.NotNull(result);
            Assert.Equal(request.PlayerId, result.Initiator);
            Assert.Equal(request.CardsToExchange, result.CardOffered);
            Assert.Equal(request.CardsToReceive, result.CardWanted);
            Assert.True(result.IsActive);
        }

        [Fact]
        public void GetNegotiationStatus_ShouldReturnCorrectNegotiation()
        {
            // Arrange
            var request = new NegotiationRequest(
                Guid.NewGuid(), // PlayerId
                Guid.NewGuid(), // NegotiationId
                new List<Card> { Card.BlackEyedBean() }, // CardsToExchange
                new List<Card> { Card.ChiliBean() } // CardsToReceive
            );
            var negotiation = _negotiationService.StartNegotiation(request);

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
            var request = new NegotiationRequest(
                Guid.NewGuid(), // PlayerId
                Guid.NewGuid(), // NegotiationId
                new List<Card> { Card.BlackEyedBean() }, // CardsToExchange
                new List<Card> { Card.ChiliBean() } // CardsToReceive
            );
            var negotiation = _negotiationService.StartNegotiation(request);
            negotiation.OfferAccepted = true;

            var responseRequest = new ResponseToOfferRequest(
                request.PlayerId, // PlayerId
                negotiation.Id, // NegotiationId
                true // OfferAccepted
            );

            // Act
            var result = await _negotiationService.RespondToNegotiationAsync(responseRequest);

            // Assert
            Assert.Equal(OfferStatus.Accepted, result.OfferStatus);
            Assert.Equal(negotiation.CardOffered, result.CardsExchanged);
            Assert.Equal(negotiation.CardWanted, result.CardsReceived);
        }

        [Fact]
        public async Task RespondToNegotiationAsync_ShouldReturnDeclinedOffer()
        {
            // Arrange
            var request = new NegotiationRequest(
                Guid.NewGuid(), // PlayerId
                Guid.NewGuid(), // NegotiationId
                new List<Card> { Card.BlackEyedBean() }, // CardsToExchange
                new List<Card> { Card.ChiliBean() } // CardsToReceive
            );
            var negotiation = _negotiationService.StartNegotiation(request);
            negotiation.OfferAccepted = false;

            var responseRequest = new ResponseToOfferRequest(
                request.PlayerId, // PlayerId
                negotiation.Id, // NegotiationId
                false // OfferAccepted
            );

            // Act
            var result = await _negotiationService.RespondToNegotiationAsync(responseRequest);

            // Assert
            Assert.Equal(OfferStatus.Declined, result.OfferStatus);
            Assert.Equal(negotiation.CardWanted, result.CardsExchanged);
            Assert.Equal(negotiation.CardOffered, result.CardsReceived);
        }

        [Fact]
        public void EndNegotiation_ShouldSetNegotiationToInactive()
        {
            // Arrange
            var request = new NegotiationRequest(
                Guid.NewGuid(), // PlayerId
                Guid.NewGuid(), // NegotiationId
                new List<Card> { Card.BlackEyedBean() }, // CardsToExchange
                new List<Card> { Card.ChiliBean() } // CardsToReceive
            );
            var negotiation = _negotiationService.StartNegotiation(request);

            // Act
            _negotiationService.EndNegotiation(negotiation);

            // Assert
            Assert.False(negotiation.IsActive);
        }
    }
}
