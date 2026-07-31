using System.Collections.Concurrent;
using System.Security.Cryptography;
using System.Text;
using WorkflowPlatform.Application.ReadModel;

namespace WorkflowPlatform.Api.Infrastructure;

public sealed class InMemoryCaseHistoryStore : ICaseHistoryStore
{
    private readonly ConcurrentDictionary<Guid, List<InternalEntry>> _entries = new();

    private sealed class InternalEntry
    {
        public required CaseHistoryEntry Entry { get; init; }
        public string Checksum { get; set; } = string.Empty;
        public string? PreviousChecksum { get; set; }
    }

    public void Append(CaseHistoryEntry entry)
    {
        var list = _entries.GetOrAdd(entry.CaseId, _ => new());
        string? prevChecksum = null;
        lock (list)
        {
            if (list.Count > 0) prevChecksum = list[^1].Checksum;
            var checksum = ComputeChecksum(prevChecksum, entry);
            list.Add(new InternalEntry { Entry = entry, Checksum = checksum, PreviousChecksum = prevChecksum });
        }
    }

    public IReadOnlyList<CaseHistoryEntry> List(Guid caseId)
    {
        if (_entries.TryGetValue(caseId, out var list))
        {
            lock (list) return list.Select(e => e.Entry).ToList();
        }
        return Array.Empty<CaseHistoryEntry>();
    }

    public bool VerifyIntegrity(Guid caseId)
    {
        if (!_entries.TryGetValue(caseId, out var list)) return true;
        lock (list)
        {
            for (var i = 0; i < list.Count; i++)
            {
                var expected = ComputeChecksum(i > 0 ? list[i - 1].Checksum : null, list[i].Entry);
                if (!string.Equals(expected, list[i].Checksum, StringComparison.OrdinalIgnoreCase))
                    return false;
            }
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
