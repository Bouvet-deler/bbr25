namespace SharedModels;

public class Card
{
    //Kort må identifiseres, fordi vi må respektere rekkefølge
    public Guid Id;
    public string Type;
    public int TotalNumberOfType;

    public readonly List<Tuple<int, int>> ExchangeMap;
    public int Harvest(int numberOfCards)
    {
        foreach (var item in ExchangeMap)
        {
            if (numberOfCards >= item.Item1)
            {
                return item.Item2;
            }

        }
        return 0;
    }
    private Card(string type, int totalNumberOfType, List<Tuple<int, int>> exchangeMap)
    {
        Type = type;
        TotalNumberOfType = totalNumberOfType;
        ExchangeMap = exchangeMap;
        Id = Guid.NewGuid();
    }
    public static Card BlackEyedBean()
    {
        var exchangeMap = new List<Tuple<int, int>>{
        new Tuple<int, int>(6,4),
        new Tuple<int, int>(5,3),
        new Tuple<int, int>(4,2),
        new Tuple<int, int>(2,1),
    };
        //Ensure ordering
        var card = new Card("Marshwaganda",10, exchangeMap);
        return card;
    }
    public static Card ChiliBean()
    {
        var exchangeMap = new List<Tuple<int, int>>{
        new Tuple<int, int>(9,4),
        new Tuple<int, int>(8,3),
        new Tuple<int, int>(6,2),
        new Tuple<int, int>(3,1)
    };
        //Ensure ordering
        var card = new Card("Plutos Mane",18, exchangeMap);
        return card;
    }
    public static Card BlueBean()
    {
        var exchangeMap = new List<Tuple<int, int>>{
        new Tuple<int, int>(10,4),
        new Tuple<int, int>(8,3),
        new Tuple<int, int>(6,2),
        new Tuple<int, int>(4,1)
    };
        //Ensure ordering
        var card = new Card("Venusvamp", 20, exchangeMap);
        return card;
    }
    public static Card RedBean()
    {
        var exchangeMap = new List<Tuple<int, int>>{
        new Tuple<int, int>(5,4),
        new Tuple<int, int>(4,3),
        new Tuple<int, int>(3,2),
        new Tuple<int, int>(2,1)
    };
        //Ensure ordering
        var card = new Card("Uranuceps",8, exchangeMap);
        return card;
    }
    public static Card SoyBean()
    {
        var exchangeMap = new List<Tuple<int, int>>{
        new Tuple<int, int>(7,4),
        new Tuple<int, int>(6,3),
        new Tuple<int, int>(4,2),
        new Tuple<int, int>(2,1)
    };
        //Ensure ordering
        var card = new Card("Saturnjong", 12,exchangeMap);
        return card;
    }
    public static Card StinkBean()
    {
        var exchangeMap = new List<Tuple<int, int>>{
        new Tuple<int, int>(8,4),
        new Tuple<int, int>(7,3),
        new Tuple<int, int>(5,2),
        new Tuple<int, int>(3,1)
    };
        //Ensure ordering
        var card = new Card("Jupitail", 16, exchangeMap);
        return card;
    }
    public static Card GreenBean()
    {
        var exchangeMap = new List<Tuple<int, int>>{
        new Tuple<int, int>(7,4),
        new Tuple<int, int>(6,3),
        new Tuple<int, int>(5,2),
        new Tuple<int, int>(3,1)
    };
        //Ensure ordering
        var card = new Card("Jordflue",14, exchangeMap);
        return card;
    }
    public static Card GardenBean()
    {
        var exchangeMap = new List<Tuple<int, int>>{
        new Tuple<int, int>(3,3),
        new Tuple<int, int>(2,2)
    };
        //Ensure ordering
        var card = new Card("Merkubello",6, exchangeMap);
        return card;
    }
}
