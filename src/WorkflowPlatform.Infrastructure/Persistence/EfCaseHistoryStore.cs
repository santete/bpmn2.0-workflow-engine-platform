using Microsoft.EntityFrameworkCore;
using WorkflowPlatform.Application.ReadModel;

namespace WorkflowPlatform.Infrastructure.Persistence;

public sealed class EfCaseHistoryStore : ICaseHistoryStore
{
    private readonly IDbContextFactory<AppDbContext> _factory;

    public EfCaseHistoryStore(IDbContextFactory<AppDbContext> factory) => _factory = factory;

    public void Append(CaseHistoryEntry entry)
    {
        using var ctx = _factory.CreateDbContext();
        ctx.CaseHistories.Add(new CaseHistoryRecord
        {
            CaseId = entry.CaseId.ToString(),
            Kind = entry.Kind.ToString(),
            TaskId = entry.TaskId,
            TaskName = entry.TaskName,
            Actor = entry.Actor,
            Decision = entry.Decision,
            OccurredAt = entry.OccurredAt
        });
        ctx.SaveChanges();
    }

    public IReadOnlyList<CaseHistoryEntry> List(Guid caseId)
    {
        using var ctx = _factory.CreateDbContext();
        return ctx.CaseHistories
            .AsNoTracking()
            .Where(h => h.CaseId == caseId.ToString())
            .OrderBy(h => h.Id)
            .Select(h => new CaseHistoryEntry(
                Guid.Parse(h.CaseId),
                Enum.Parse<CaseHistoryKind>(h.Kind),
                h.TaskId, h.TaskName, h.Actor, h.Decision, h.OccurredAt))
            .ToList();
    }
}
