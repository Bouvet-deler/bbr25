namespace BoardGameServer.Application;

public interface IRegisterActions
{
    Guid Join(string name);
    void StartGame();
}
