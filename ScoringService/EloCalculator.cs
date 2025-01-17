namespace ScoringService
{

    /// <summary>
    /// Denne kom inn i eksistens fordi jeg trengte å dumpe resultatet av en runde før
    /// jeg sendte den videre til et nytt spill
    /// </summary>
    public class EloCalculator
    {
        private readonly int _k = 30;
        public readonly IScoreRepository ScoreRepository;

        public EloCalculator(IScoreRepository scoreRepository)
        {

            ScoreRepository = scoreRepository;
        }

        /// <summary>
        /// Implementering av SimpleMultiplayerElo
        /// http://www.tckerrigan.com/Misc/Multiplayer_Elo/
        /// At the end of a game, make a list of all the players and sort it by performance.
        /// Think of each player as having played two matches: a loss vs. the player right above him on the list, and a win vs. the player right below him.
        /// Update each player's rating accordingly using the two-player Elo equations.
        ///
        /// Det blir sikkert strengt tatt galt å gjøre dette "in-place", men jeg driter i
        /// det for nå
        /// </summary>
        /// <param name="ranking">Rekkefølgen på spillerene </param>
        /// <returns></returns>
        public void ScoreGame(List<string> ranking)
        {
            //The matches
            for(int i = 0; i < ranking.Count()-1;i++)
            {
                var name1 = ranking[i];
                var name2 = ranking[i+1];
                int elo1 = ScoreRepository.GetScoreByName(name1);
                int elo2 = ScoreRepository.GetScoreByName(name2);
                double probability1 = (1.0 /(1.0 + Math.Pow(10, (elo2 - elo1)/100.0)));
                double probability2 = (1.0 /(1.0 + Math.Pow(10, (elo1 - elo2)/100.0)));
                Console.WriteLine(probability2);
                // Vi vet at den som kommer først var den som vant, siden vi har sortert
                int newElo1 = (int)(elo1 + _k*(1.0 - probability1)); 
                int newElo2 = (int)(elo2 + _k*(0.0 - probability2));
                Console.WriteLine((int)_k*(1.0 - probability1));
                ScoreRepository.UpdateScore(name1, newElo1);
                ScoreRepository.UpdateScore(name2, newElo2);
            }
        }
    }
}
