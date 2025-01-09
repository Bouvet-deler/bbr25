namespace BoardGameServer.Application;
public enum Phase
{
    Planting,
    PlantingOptional,
    Trading,
    TradePlanting,
}
public static class PhaseUtil
{
    public static string GetDescription(Phase phase)
    {
        switch (phase)
        {
            case Phase.Planting:
                return "Planting";
            case Phase.PlantingOptional:
                return "PlantingOptional";
            case Phase.Trading:
                return "Trading";
            case Phase.TradePlanting:
                return "TradePlanting";
            default:
                return "Undefined phase";
        }
    }
}
