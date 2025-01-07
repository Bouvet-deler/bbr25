using SharedModels;

namespace BoardGameServer.Application.Services
{
    public class GameService
    {
        private readonly Game _game;
        
        public GameService()
        {
            _game = new Game();
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
