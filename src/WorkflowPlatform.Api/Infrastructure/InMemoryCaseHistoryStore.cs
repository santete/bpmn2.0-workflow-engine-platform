using System.Collections.Concurrent;
using WorkflowPlatform.Application.ReadModel;

namespace WorkflowPlatform.Api.Infrastructure;

public sealed class InMemoryCaseHistoryStore : ICaseHistoryStore
{
    private readonly ConcurrentDictionary<Guid, List<CaseHistoryEntry>> _entries = new();

    public void Append(CaseHistoryEntry entry)
    {
        _entries.GetOrAdd(entry.CaseId, _ => new()).Add(entry);
    }

    public IReadOnlyList<CaseHistoryEntry> List(Guid caseId)
    {
        if (_entries.TryGetValue(caseId, out var list))
        {
            lock (list) return list.ToList();
        }
        return Array.Empty<CaseHistoryEntry>();
    }
}
