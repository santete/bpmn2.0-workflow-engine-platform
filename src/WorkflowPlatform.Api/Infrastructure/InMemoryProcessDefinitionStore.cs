using System.Collections.Concurrent;
using WorkflowPlatform.Application.Definitions;

namespace WorkflowPlatform.Api.Infrastructure;

public sealed class InMemoryProcessDefinitionStore : IProcessDefinitionStore
{
    private readonly ConcurrentDictionary<string, ProcessDefinitionSpec> _defs = new();

    public void Save(ProcessDefinitionSpec spec) => _defs[spec.Key] = spec;
    public ProcessDefinitionSpec? Get(string key) => _defs.TryGetValue(key, out var s) ? s : null;
    public IReadOnlyList<ProcessDefinitionSpec> All() => _defs.Values.ToList();
}
