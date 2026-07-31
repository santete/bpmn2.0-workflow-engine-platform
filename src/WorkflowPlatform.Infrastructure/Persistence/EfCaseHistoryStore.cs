using System.Security.Cryptography;
using System.Text;
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
        var last = ctx.CaseHistories
            .Where(h => h.CaseId == entry.CaseId.ToString())
            .OrderByDescending(h => h.Id)
            .Select(h => h.Checksum)
            .FirstOrDefault();

        var checksum = ComputeChecksum(last, entry);
        ctx.CaseHistories.Add(new CaseHistoryRecord
        {
            CaseId = entry.CaseId.ToString(),
            Kind = entry.Kind.ToString(),
            TaskId = entry.TaskId,
            TaskName = entry.TaskName,
            Actor = entry.Actor,
            Decision = entry.Decision,
            OccurredAt = entry.OccurredAt,
            Checksum = checksum,
            PreviousChecksum = last
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

    public bool VerifyIntegrity(Guid caseId)
    {
        using var ctx = _factory.CreateDbContext();
        var records = ctx.CaseHistories
            .Where(h => h.CaseId == caseId.ToString())
            .OrderBy(h => h.Id)
            .Select(h => new { h.Kind, h.TaskId, h.TaskName, h.Actor, h.Decision, h.OccurredAt, h.Checksum, h.PreviousChecksum })
            .ToList();

        for (var i = 0; i < records.Count; i++)
        {
            var reconstructed = new CaseHistoryEntry(
                caseId,
                Enum.Parse<CaseHistoryKind>(records[i].Kind),
                records[i].TaskId, records[i].TaskName,
                records[i].Actor, records[i].Decision,
                records[i].OccurredAt);
            var expected = ComputeChecksum(records[i].PreviousChecksum, reconstructed);
            if (!string.Equals(expected, records[i].Checksum, StringComparison.OrdinalIgnoreCase))
                return false;
        }
        return true;
    }

    private static string ComputeChecksum(string? prev, CaseHistoryEntry entry)
    {
        var raw = $"{(prev ?? "0")}|{entry.CaseId}|{entry.Kind}|{entry.TaskId}|{entry.TaskName}|{entry.Actor}|{entry.Decision}|{entry.OccurredAt:O}";
        var hash = SHA256.HashData(Encoding.UTF8.GetBytes(raw));
        return Convert.ToHexStringLower(hash);
    }
}
