using System.Collections.Concurrent;
using WorkflowPlatform.Domain.Cases;

namespace WorkflowPlatform.Api.Infrastructure;

public sealed class InMemoryCaseRepository : ICaseRepository
{
    private readonly ConcurrentDictionary<Guid, Case> _store = new();

    public void Add(Case @case) => _store[@case.Id] = @case;
    public void Save(Case @case) => _store[@case.Id] = @case;
    public Case? Get(Guid id) => _store.TryGetValue(id, out var c) ? c : null;
    public IReadOnlyList<Case> All() => _store.Values.ToList();
}
