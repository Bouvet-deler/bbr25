
using BoardGameServerSimple.Models;

namespace BoardGameServerSimple.Services;

public class GameStateManager
{
    private GameState _gameState;

    public void StartGame()
    {
        _gameState = new GameState();
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
