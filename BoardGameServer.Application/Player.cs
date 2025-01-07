using SharedModels;

namespace BoardGameServer.Application
{
    public class Player
    {
        // Id til spillere.
        public Guid Id; 

        //Spiller som skal spille etter denne
        public Player? NextPlayer = null;

        //Kort som kun skal vises til denne spilleren.
        public Queue<Card> Hand = new Queue<Card>();

        //Beholder for kortene som man har byttet til seg ila trading fasen
        public List<Card> TradedCards = new List<Card>();
        
        //Kors som ble trukket i starten av byttefasen
        public List<Card> DrawnCards = new List<Card>();

        //Der spilleren kan så sine bønner
        public Dictionary<Guid, List<Card>> Fields = new Dictionary<Guid, List<Card>>();

        //Er spilleren startspiller?
        public bool StartingPlayer;

        //
        public int Coins = 0;
        //Egenregistrert navn
        public string? Name;

        public Player(string name)
        {
            Id = Guid.NewGuid();
            Name = name;
        }

    }
}
