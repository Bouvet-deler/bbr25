namespace BoardGameServer.Application;

public interface IRegisterActions
{
    Guid Join(string name, string playerId);
    void StartGame();
}
