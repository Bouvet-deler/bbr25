using ScoringService;

var scoreRepo = new ScoreRepository();
var scoreService = new EloCalculator(scoreRepo);

var player1 = "Player1";
var player2 = "Player2";
var player3 = "Player3";
var player4 = "Player4";
scoreRepo.NewPlayer(player1);
scoreRepo.NewPlayer(player2);
scoreRepo.NewPlayer(player3);
scoreRepo.NewPlayer(player4);

List<string>ranking  = [player2, player1, player3];

for (int i = 0; i < 100; i++)
{
    scoreService.ScoreGame(ranking);
}

scoreRepo.PrintAllScores();
