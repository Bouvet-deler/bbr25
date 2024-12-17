
using BoardGameServerSimple.Models;

namespace BoardGameServerSimple.Services;

public class GameStateManager
{
    private GameState _gameState;
    private readonly GameStateFactory _gameStateFactory;

    public GameStateManager(GameStateFactory gameStateFactory)
    {
        _gameStateFactory = gameStateFactory;
        _gameState = _gameStateFactory.CreateNewGameState();
    }

    public void StartGame()
    {
        _gameState = _gameStateFactory.CreateNewGameState();
    }

    internal GameState GetGameState()
    {
        return _gameState;
    }

    internal int GetPlayerScore(int playerId)
    {
        return 0;
    }

    internal Task PlayCard(Card card)
    {
        throw new NotImplementedException();
    }
}
