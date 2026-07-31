using Microsoft.EntityFrameworkCore;
using WorkflowPlatform.Workflow.Adapter.Replay;

namespace WorkflowPlatform.Infrastructure.Persistence;

/// <summary>IReplayLogStore trên EF Core → nhật ký tiến trình sống sót qua restart.</summary>
public sealed class EfReplayLogStore : IReplayLogStore
{
    private readonly IDbContextFactory<AppDbContext> _factory;

    public EfReplayLogStore(IDbContextFactory<AppDbContext> factory) => _factory = factory;

    public void EnsureInstance(string businessKey, string definitionKey)
    {
        using var ctx = _factory.CreateDbContext();
        if (!ctx.ReplayInstances.Any(x => x.BusinessKey == businessKey))
        {
            ctx.ReplayInstances.Add(new ReplayInstanceRecord { BusinessKey = businessKey, DefinitionKey = definitionKey });
            ctx.SaveChanges();
        }
    }

    public string? GetDefinitionKey(string businessKey)
    {
        using var ctx = _factory.CreateDbContext();
        return ctx.ReplayInstances.AsNoTracking().FirstOrDefault(x => x.BusinessKey == businessKey)?.DefinitionKey;
    }

    public IReadOnlyList<CompletionEntry> GetCompletions(string businessKey)
    {
        using var ctx = _factory.CreateDbContext();
        return ctx.ReplayCompletions.AsNoTracking()
            .Where(x => x.BusinessKey == businessKey)
            .OrderBy(x => x.Seq)
            .Select(x => new CompletionEntry(x.TaskId, x.Decision))
            .ToList();
    }

    public void Append(string businessKey, string taskId, string? decision)
    {
        using var ctx = _factory.CreateDbContext();
        var seq = ctx.ReplayCompletions.Count(x => x.BusinessKey == businessKey);
        ctx.ReplayCompletions.Add(new ReplayCompletionRecord
        {
            BusinessKey = businessKey, Seq = seq, TaskId = taskId, Decision = decision
        });
        ctx.SaveChanges();
    }

    public bool IsCancelled(string businessKey)
    {
        using var ctx = _factory.CreateDbContext();
        return ctx.ReplayInstances
            .AsNoTracking()
            .Any(x => x.BusinessKey == businessKey && x.IsCancelled);
    }

    public void Cancel(string businessKey)
    {
        using var ctx = _factory.CreateDbContext();
        var ri = ctx.ReplayInstances.FirstOrDefault(x => x.BusinessKey == businessKey);
        if (ri is not null)
        {
            ri.IsCancelled = true;
            ctx.SaveChanges();
        }
    }
}
