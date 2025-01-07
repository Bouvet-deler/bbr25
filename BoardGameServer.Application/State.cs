namespace BoardGameServer.Application;

public enum State
{
    Registering,
    Playing,
    GameDone,
}
    public static class StateUtil
    {
        public static string GetDescription(State phase)
        {
            switch (phase)
            {
                case State.Registering:
                    return "Registering";
                case State.Playing:
                    return "Playing";
                case State.GameDone:
                    return "GameDone";
                default:
                    return "Undefined state";
            }
        }
    }
