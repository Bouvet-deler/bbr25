using BoardGameServer.Application;
using BoardGameServer.Application.Models;
using SharedModels;

public class ValidationRules
{

    public ValidationRules()
    {}

    public void StartGameValidation(Game game,IDictionary<string, string[]> errors)
    {
       NotAlreadyStarted(game,errors); 
    }
    public void JoinGameValidation(Game game,string name,IDictionary<string, string[]> errors)
    {
       NotAlreadyJoined(game,name,errors); 
       Max5Players(game,errors); 
    }
    public void EndPlantingValidation(Game game, Player player, IDictionary<string, string[]> errors)
    {
        IsCurrentPlayer(game, player, errors);
        IsInPlayingState(game, errors);
        IsInPlantingPhase(game, player, errors);
    }
    public void EndTradingValidation(Game game, Player player, IDictionary<string, string[]> errors)
    {
        IsInPlayingState(game, errors);
        IsCurrentPlayer(game, player, errors);
        IsInTradingPhase(game, errors);
    }
    public void HarvestFieldValidation(Game game, Player player, Guid field, IDictionary<string, string[]> errors)
    {
        IsInPlayingState(game, errors);
        FieldIsValid(player, field, errors);
        RuleOfBeanProtection(game, player, field, errors);
    }

    public void PlantingPhaseValidation(Game game, Player player, Guid field, IDictionary<string,string[]> errors)
    {
        IsInPlayingState(game, errors);
        IsInPlantingPhase(game, player, errors);
        IsCurrentPlayer(game, player, errors);
        FieldIsValid(player, field, errors);
        FieldIsPlayable(player, player.Hand.First(), field, errors);
    }

    public void TradePlantingPhaseValidation(Game game, Player player, Guid card, Guid field, IDictionary<string, string[]> errors)
    {
        IsInPlayingState(game, errors);
        IsInTradePlantingPhase(game, player, errors);
        TradePlantIsValid(game, player, card, errors);
        FieldIsPlayable(player,player.DrawnCards.Where(c => c.Id == card).Union(player.TradedCards.Where(c => c.Id == card)).Single() , field, errors);
    }

    public void AcceptTradeValidation(Game game, Player player,Offer offer, Accept accept, IDictionary<string, string[]> errors)
    {
        IsInPlayingState(game, errors);
        IsInTradingPhase(game, errors);
        OnePlayerIsCurrent(game,player, offer, accept, errors);
    }
    public void RequestTradeValidation(Game game, Player player, Offer negotiationRequest, IDictionary<string, string[]> errors)
    {
        IsInPlayingState(game, errors);
        IsCurrentPlayer(game, player, errors);
        IsInTradingPhase(game, errors);
    }
     public void NotAlreadyStarted(Game game,IDictionary<string, string[]> errors)
    {
        if (game.CurrentState != State.Registering)
        {
            errors["Teknisk regel"] = ["du kan bare starte spillet i registreringsfasen"];
        }
    }
    private void NotAlreadyJoined(Game game,string name,IDictionary<string, string[]> errors)
    {
        if (game.Players.Any(kv => kv.Name == name))
        {
            errors["Teknisk regel"] = ["du kan bare joine spillet en gang"];
        }
    }
    private void Max5Players(Game game,IDictionary<string, string[]> errors)
    {
        if (game.Players.Count >4)
        {
            errors["Teknisk regel"] = ["du kan bare joine spillet en gang"];
        }
    }
    public void OnePlayerIsCurrent(Game game, Player player,Offer offer,  Accept accept, IDictionary<string, string[]> errors)
    {
        if (game.CurrentPlayer.Id != offer.InitiatorId && game.CurrentPlayer.Id != player.Id)
        {
            errors["Spillregel N"] = ["Den aktive spilleren må være en del av et bytte"];
        }
    }

    private void RuleOfBeanProtection(Game game, Player player, Guid field, IDictionary<string, string[]> errors)
    {
        //Om du prøver å høste et felt med bare en bønne, kan du bare gjøre det om ingen
        //andre felter har 2 eller fler bønner på seg
        if (player.Fields[field].Count() == 1)
        {
            if(player.Fields.Any(list => list.Value.Count() > 1))
            {
                errors["Spillregel 14"] = ["Regel for bønners beskyttelse"];
            }
        }
    }

    private static void IsInTradingPhase(Game game, IDictionary<string, string[]> errors)
    {
        if( game.CurrentState != State.Playing)
        {
            errors["Teknisk regel 3"] = ["CurrentPhase må være Trading for å kunne avslutte trading fasen"];
        }
    }

    private static void IsInPlayingState(Game game, IDictionary<string, string[]> errors)
    {
        if( game.CurrentState != State.Playing)
        {
            errors["Teknisk regel 1"] = ["CurrentState må være Playing for å kunne gjøre spill-handlinger"];
        }
    }

    private void IsInTradePlantingPhase(Game game, Player player, IDictionary<string, string[]> errors)
    {
        if( game.CurrentPhase != Phase.TradePlanting)
        {
            errors["Teknisk regel 3"] = ["CurrentPhase må være Planting eller PlantingOptional for å kunne gjøre en plant"];
        }
    }

    private void IsInPlantingPhase(Game game, Player player, IDictionary<string, string[]> errors)
    {
        if( !(game.CurrentPhase == Phase.Planting || game.CurrentPhase == Phase.PlantingOptional))
        {
            errors["Teknisk regel 3"] = ["CurrentPhase må være Planting eller PlantingOptional for å kunne gjøre en plant"];
        }
    }

    private void IsCurrentPlayer(Game game, Player player, IDictionary<string, string[]> errors)
    {
        if(game.CurrentPlayer.Id != player.Id)
        {
            errors["Teknisk regel 2"] = ["Du kan bare gjøre handlinger på din tur"];
        }
    }

    private void TradePlantIsValid(Game game, Player player, Guid card, IDictionary<string, string[]> errors)
    {
        if(!(player.DrawnCards.Any(c => c.Id == card) || player.TradedCards.Any(c => c.Id == card)))
        {
            errors["Teknisk regel 3"] = ["Kortet du forsøkte å plante finnes ikke i de trukkede eller byttede kortene"];
        } 
    }

    private void  TradeExists(Game player, Guid tradeId, IDictionary<string, string[]> errors)
    {
        if(!player.TradingArea.Any(o=>o.NegotiationId == tradeId))
        {
            errors["Teknisk regel 4"] = ["Du har oppgitt et offer  som ikke eksisterer"];
        }
    }
    private void FieldIsValid(Player player, Guid field, IDictionary<string, string[]> errors)
    {
        if(!player.Fields.ContainsKey(field))
        {
            errors["Teknisk regel 4"] = ["Du har oppgitt et field som ikke eksisterer"];
        }
    }

    private void FieldIsPlayable(Player player, Card card, Guid field, IDictionary<string, string[]> errors)
    {
        Card cardInField = player.Fields[field].FirstOrDefault();
        if (cardInField != null)
        {
            if(cardInField.Type != card.Type)
            {

            errors["Spillregel 1"] = ["Dette feltet har en annen bønnetype i seg"];
            }
        }
        //Hent kort i feltet og sjekk typen
    }
}
