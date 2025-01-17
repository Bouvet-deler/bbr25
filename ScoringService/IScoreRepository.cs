
namespace ScoringService
{
    public interface IScoreRepository
    {
        public int GetScoreByName(string name);
        public void UpdateScore(string name, int newScore);
        public IDictionary<string, int> GetScores();
        public string GetNameByGuid(Guid g);
        public void NewPlayer(string name, Guid g);
    }

    public class ScoreRepository : IScoreRepository
    {
        IDictionary<string, int> eloScores = new Dictionary<string, int>();
        IDictionary<Guid,string> guids = new Dictionary<Guid,string >();

        public ScoreRepository()
        {
        }

        public void NewPlayer(string name,Guid g )
        {
            guids[g] = name;
            eloScores[name] = 400;
        }
        public string GetNameByGuid(Guid g)
        {
            return guids[g];
        }
        public int GetScoreByName(string name)
        {
            return eloScores[name];
        }

        public void UpdateScore(string name, int newScore)
        {
            eloScores[name] = newScore;
        }
        
        public IDictionary<string, int> GetScores()
        {
            return eloScores;
        }
        public void PrintAllScores()
        {
            foreach(var kv in eloScores)
            {
                Console.WriteLine(kv.Key + ": "+kv.Value);
            }
        }

    }
}
