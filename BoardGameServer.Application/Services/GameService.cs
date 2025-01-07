using Negotiator;
using SharedModels;

namespace BoardGameServer.Application.Services
{
    public class GameService
    {
        private readonly Game _game;
        private readonly INegotiationService _negotiationService;

        public GameService(INegotiationService negotiationService)
        {
            _negotiationService = negotiationService;
            _game = new Game(_negotiationService);
        }

        public Game GetCurrentGame()
        {
            return _game;
        }

        public PlayerStatus GetStatusPlayer(Guid playerId)
        {
            //Get game by id
            return new PlayerStatus();
        }
    }
}
