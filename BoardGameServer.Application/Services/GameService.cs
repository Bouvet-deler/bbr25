using ScoringService;
using Negotiator;
using SharedModels;

namespace BoardGameServer.Application.Services
{
    public class GameService
    {
        Lock _lock = new Lock();
        private readonly Game _game;

        public GameService(EloCalculator elocalculator)
        {
            _game = new Game( elocalculator);
        }

        public Game GetCurrentGame()
        {
            lock(_lock)
            {
            }
            return _game;
        }

        public PlayerStatus GetStatusPlayer(Guid playerId)
        {
            //Get game by id
            return new PlayerStatus();
        }
    }
}
