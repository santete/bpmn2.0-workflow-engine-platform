namespace WorkflowPlatform.Workflow.Adapter.Replay;

public sealed record CompletionEntry(string TaskId, string? Decision);

/// <summary>
/// Kho nhật ký của engine Replay (SPI của adapter này). In-memory cho test; EF cho chạy thật →
/// vị trí tiến trình sống sót qua restart mà không đổi engine/domain.
/// </summary>
public interface IReplayLogStore
{
    void EnsureInstance(string businessKey, string definitionKey);
    string? GetDefinitionKey(string businessKey);
    IReadOnlyList<CompletionEntry> GetCompletions(string businessKey);
    void Append(string businessKey, string taskId, string? decision);
    bool IsCancelled(string businessKey);
    void Cancel(string businessKey);
}

/// <summary>Mặc định in-memory (test / chế độ không persistence).</summary>
public sealed class InMemoryReplayLogStore : IReplayLogStore
{
    private readonly Dictionary<string, string> _defByKey = new();
    private readonly Dictionary<string, List<CompletionEntry>> _log = new();
    private readonly HashSet<string> _cancelled = new();
    private readonly object _gate = new();

    public void EnsureInstance(string businessKey, string definitionKey)
    {
        lock (_gate)
        {
            _defByKey[businessKey] = definitionKey;
            if (!_log.ContainsKey(businessKey)) _log[businessKey] = new List<CompletionEntry>();
        }
    }

    public string? GetDefinitionKey(string businessKey)
    {
        lock (_gate) return _defByKey.TryGetValue(businessKey, out var d) ? d : null;
    }

    public IReadOnlyList<CompletionEntry> GetCompletions(string businessKey)
    {
        lock (_gate) return _log.TryGetValue(businessKey, out var l) ? l.ToList() : new List<CompletionEntry>();
    }

    public void Append(string businessKey, string taskId, string? decision)
    {
        lock (_gate)
        {
            if (!_log.TryGetValue(businessKey, out var l)) { l = new List<CompletionEntry>(); _log[businessKey] = l; }
            l.Add(new CompletionEntry(taskId, decision));
        }
    }

    public bool IsCancelled(string businessKey)
    {
        lock (_gate) return _cancelled.Contains(businessKey);
    }

    public void Cancel(string businessKey)
    {
        lock (_gate) _cancelled.Add(businessKey);
    }
}
