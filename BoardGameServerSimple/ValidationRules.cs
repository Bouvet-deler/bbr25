using BoardGameServer.Application;
using SharedModels;

public class ValidationRules
{

    public ValidationRules()
    {

    }

    public void HarvestBeanValidation(Game game, Player player, Guid field, IDictionary<string, string[]> errors)
    {
        //Om du prøver å høste et felt med bare en bønne, kan du bare gjøre det om ingen
        //andre felter har 2 eller fler bønner på seg
        if (player.Fields[field].Count() == 1)
        {
            if(player.Fields.Any(list => list.Value.Count() > 1))
            {
                errors["f"] = ["Regel for bønners beskyttelse"];
            }
        }

        IsInPlayingState(game, errors);

    }

    public void PlantingPhaseValidation(Game game, Player player, Guid field, IDictionary<string,string[]> errors)
    {
        //En spiller har ikke kort i hånden

        IsInPlayingState(game, errors);

        IsInPlantingPhase(game, player, errors);

        IsCurrentPlayer(game, player, errors);

        FieldIsValid(player, field, errors);

        FieldIsPlayable(player, player.Hand.Peek(), field, errors);

    }

    public void TradePlantingPhaseValidation(Game game, Player player, Guid field, IDictionary<string, string[]> errors)
    {
        IsInPlayingState(game, errors);

        IsInTradePlantingPhase(game, player, errors);

        TradePlantIsValid(game, player, field, errors);

        FieldIsPlayable(player, player.Hand.Peek(), field, errors);

    }

    private static void IsInPlayingState(Game game, IDictionary<string, string[]> errors)
    {
        if( game.CurrentState != State.Playing)
        {
            errors["CurrentState"] = ["CurrentState må være Playing for å kunne gjøre spill-handlinger"];
        }
    }

    private void IsInTradePlantingPhase(Game game, Player player, IDictionary<string, string[]> errors)
    {
        if( game.CurrentPhase != Phase.TradePlanting)
        {
            errors["CurrentPhase"] = ["CurrentPhase må være Planting eller PlantingOptional for å kunne gjøre en plant"];
        }
    }

    private void IsInPlantingPhase(Game game, Player player, IDictionary<string, string[]> errors)
    {
        if( game.CurrentPhase != Phase.Planting || game.CurrentPhase == Phase.PlantingOptional)
        {
            errors["CurrentPlayer"] = ["Du kan bare gjøre denne handlingen på din tur"];
        }
    }

    private void IsCurrentPlayer(Game game, Player player, IDictionary<string, string[]> errors)
    {
        if(game.CurrentPlayer.Id != player.Id)
        {

            errors["CurrentPlayer"] = ["Du kan bare gjøre handlinger på din tur"];
        }
    }

    private void TradePlantIsValid(Game game, Player player, Guid card, IDictionary<string, string[]> errors)
    {
        if(!( player.DrawnCards.Any(c => c.Id == card) || player.TradedCards.Any(c => c.Id == card)))
        {
            errors["Tradeplanting"] = ["Kortet du forsøkte å plante finnes ikke i de trukkede eller byttede kortene"];
        } 
    }

    private void FieldIsValid(Player player, Guid field, IDictionary<string, string[]> errors)
    {
        if(!player.Fields.ContainsKey(field))
        {
            errors["Field"] = ["Du har oppgitt et field som ikke eksisterer"];
        }
    }

    private void FieldIsPlayable(Player player, Card card, Guid field, IDictionary<string, string[]> errors)
    {
        Card cardInField = player.Fields[field].FirstOrDefault();
        if (cardInField != null)
        {
            if(cardInField.Type != card.Type)
            {

            }
        }
        //Hent kort i feltet og sjekk typen
    }
}
