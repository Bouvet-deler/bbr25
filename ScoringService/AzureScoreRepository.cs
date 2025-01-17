using Azure;
using Azure.Data.Tables;
using Microsoft.Extensions.Configuration;

namespace ScoringService;

public class AzureScoreRepository : IScoreRepository
{
    private readonly string _tableName = "BBRScoreStorage";
    private readonly string _partitionKey = "Default";
    private readonly string _scoreKey = "Score";

    private readonly TableClient _scoreTable;
    public AzureScoreRepository(IConfiguration configuration)
    {

        _scoreTable = new TableClient(configuration.GetConnectionString("ScoreConnection"), _tableName);
        _scoreTable.CreateIfNotExists();
    }

    public void NewPlayer(string name,Guid g) => _scoreTable.AddEntity(new PlayerScore()
    {
        RowKey = name,
        PartitionKey = _partitionKey,
        Score = 400,
        Guid = g
    });

    public int GetScoreByName(string name)
    {
        TableEntity entity = _scoreTable.GetEntity<TableEntity>(_partitionKey, name);
        return entity.GetInt32(_scoreKey) ?? 0;
    }


    public void UpdateScore(string name, int newScore)
    {
        TableEntity entity = _scoreTable.GetEntity<TableEntity>(_partitionKey, name);

        entity[_scoreKey] = newScore;
        _scoreTable.UpdateEntity(entity, ETag.All);
    }


    public IDictionary<string, int> GetScores()
    {
        var scores = new Dictionary<string, int>();
        var queryResults = _scoreTable.Query<TableEntity>(entity => entity.PartitionKey == _partitionKey);

        foreach (TableEntity entity in queryResults)
        {
            scores[entity.RowKey] = entity.GetInt32(_scoreKey) ?? 0;
        }

        return scores;
    }
    public string GetNameByGuid(Guid g)
    {
        var scores = new Dictionary<Guid, string>();
        var queryResults = _scoreTable.Query<PlayerScore>(entity => entity.PartitionKey == _partitionKey);

        foreach(PlayerScore entity in queryResults)
        {
            scores[entity.Guid] = entity.RowKey;
        }

        return scores[g];
    }
    public void PrintAllScores()
    {
        foreach (var entity in _scoreTable.Query<TableEntity>())
        {

            string partitionKey = entity.PartitionKey;
            string rowKey = entity.RowKey;

            int score = entity.GetInt32(_scoreKey) ?? 0;

            Console.WriteLine($"PartitionKey: {partitionKey}, Name: {rowKey}, Score: {score}");
        }
    }
}

public record PlayerScore : ITableEntity
{
    public string PartitionKey { get; set; }
    public string RowKey { get; set; }
    public int Score { get; set; }
    public Guid Guid {get; set; }
    public ETag ETag { get; set; }
    public DateTimeOffset? Timestamp { get; set; }
}
