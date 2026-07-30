using System.Collections.Concurrent;
using WorkflowPlatform.Application.ReadModel;

namespace WorkflowPlatform.Api.Infrastructure;

public sealed class InMemoryCaseReadStore : ICaseReadStore
{
    private readonly ConcurrentDictionary<Guid, CaseView> _views = new();

    public void Upsert(CaseView view) => _views[view.Id] = view;
    public CaseView? Get(Guid id) => _views.TryGetValue(id, out var v) ? v : null;
    public IReadOnlyList<CaseView> All() => _views.Values.ToList();
}
