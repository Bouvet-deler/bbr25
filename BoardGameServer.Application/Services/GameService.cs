using ScoringService;
using SharedModels;

namespace BoardGameServer.Application.Services
{
    public class GameService
    {
        IDictionary<string, Game> _games = new Dictionary<string, Game>();

        public GameService(EloCalculator elocalculator)
        {
            _games["PINK"] = new Game(elocalculator, "PINK");
            _games["BLUE"] = new Game(elocalculator, "BLUE");
        }

        public Game GetGameByName(string gameName)
        {
            return _games[gameName];
        }
        public IEnumerable<Game> GetAllGames()
        {
            return _games.Values;
        }

        public PlayerStatus GetStatusPlayer(Guid playerId)
        {
            //Get game by id
            return new PlayerStatus();
        }
    }
}
