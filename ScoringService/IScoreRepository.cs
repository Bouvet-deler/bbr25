
namespace ScoringService
{
    public interface IScoreRepository
    {
        public int GetScoreByName(string name);
        public void UpdateScore(string name, int newScore);
        public IDictionary<string, int> GetScores();
    }

    public class ScoreRepository : IScoreRepository
    {
        IDictionary<string, int> eloScores = new Dictionary<string, int>();

        public ScoreRepository()
        {
        }

        public void NewPlayer(string name)
        {
            eloScores[name] = 400;
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
