using ScoringService;
using SharedModels;

namespace BoardGameServer.Application.Services
{
    public class GameService
    {
        IDictionary<string, Game> _games = new Dictionary<string, Game>();

        public GameService(EloCalculator elocalculator)
        {
            _games["GAME1"] = new Game(elocalculator, "GAME1");
            _games["GAME2"] = new Game(elocalculator, "GAME2");
            _games["GAME3"] = new Game(elocalculator, "GAME3");
            _games["GAME4"] = new Game(elocalculator, "GAME4");
            _games["GAME5"] = new Game(elocalculator, "GAME5");
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
