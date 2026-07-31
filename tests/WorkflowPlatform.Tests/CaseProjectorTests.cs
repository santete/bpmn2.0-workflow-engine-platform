using WorkflowPlatform.Application.ReadModel;
using WorkflowPlatform.Domain.Cases;
using WorkflowPlatform.Workflow.Abstraction.Events;
using Xunit;

namespace WorkflowPlatform.Tests;

public class CaseProjectorTests
{
    private sealed class FakeReadStore : ICaseReadStore
    {
        private readonly Dictionary<Guid, CaseView> _views = new();
        public void Upsert(CaseView view) => _views[view.Id] = view;
        public CaseView? Get(Guid id) => _views.GetValueOrDefault(id);
        public IReadOnlyList<CaseView> All() => _views.Values.ToList();
    }

    private sealed class FakeRepository : ICaseRepository
    {
        private readonly Dictionary<Guid, Case> _cases = new();
        public void Add(Case @case) => _cases[@case.Id] = @case;
        public void Save(Case @case) => _cases[@case.Id] = @case;
        public Case? Get(Guid id) => _cases.GetValueOrDefault(id);
        public IReadOnlyList<Case> All() => _cases.Values.ToList();
    }

    private sealed class FakeHistoryStore : ICaseHistoryStore
    {
        public List<CaseHistoryEntry> Entries { get; } = new();
        public void Append(CaseHistoryEntry entry) => Entries.Add(entry);
        public IReadOnlyList<CaseHistoryEntry> List(Guid caseId)
            => Entries.Where(e => e.CaseId == caseId).ToList();
        public bool VerifyIntegrity(Guid caseId) => true;
    }

    private static (CaseProjector projector, FakeReadStore views, FakeHistoryStore history) Setup(Guid caseId)
    {
        var views = new FakeReadStore();
        var history = new FakeHistoryStore();
        var projector = new CaseProjector(views, new FakeRepository(), history);
        projector.OnCaseCreated(caseId, "Ho so A", "case-approval");
        return (projector, views, history);
    }

    [Fact]
    public async Task TaskCreated_sets_current_assignee_on_view()
    {
        var caseId = Guid.NewGuid();
        var (projector, views, _) = Setup(caseId);

        await projector.HandleAsync(new TaskCreated(
            caseId.ToString(), "review", "Tham dinh", "thamdinh", DateTimeOffset.UtcNow));

        Assert.Equal("thamdinh", views.Get(caseId)!.CurrentTaskAssignee);
    }

    [Fact]
    public async Task TaskCompleted_appends_history_entry()
    {
        var caseId = Guid.NewGuid();
        var (projector, _, history) = Setup(caseId);
        var at = DateTimeOffset.UtcNow;

        await projector.HandleAsync(new TaskCompleted(
            caseId.ToString(), "review", "Tham dinh", "an.nguyen", "APPROVED", at));

        var entry = Assert.Single(history.List(caseId));
        Assert.Equal(CaseHistoryKind.TaskCompleted, entry.Kind);
        Assert.Equal("review", entry.TaskId);
        Assert.Equal("Tham dinh", entry.TaskName);
        Assert.Equal("an.nguyen", entry.Actor);
        Assert.Equal("APPROVED", entry.Decision);
        Assert.Equal(at, entry.OccurredAt);
    }

    [Fact]
    public async Task ProcessCompleted_appends_outcome_entry_and_clears_task()
    {
        var caseId = Guid.NewGuid();
        var (projector, views, history) = Setup(caseId);
        await projector.HandleAsync(new TaskCreated(
            caseId.ToString(), "approve", "Phe duyet", "lanhdao", DateTimeOffset.UtcNow));

        await projector.HandleAsync(new ProcessCompleted(caseId.ToString(), DateTimeOffset.UtcNow));

        var entry = Assert.Single(history.List(caseId), e => e.Kind == CaseHistoryKind.ProcessCompleted);
        Assert.Null(entry.TaskId);
        var view = views.Get(caseId)!;
        Assert.Null(view.CurrentTaskId);
        Assert.Null(view.CurrentTaskAssignee);
    }

    [Fact]
    public async Task ProcessRejected_appends_outcome_entry()
    {
        var caseId = Guid.NewGuid();
        var (projector, _, history) = Setup(caseId);

        await projector.HandleAsync(new ProcessRejected(caseId.ToString(), DateTimeOffset.UtcNow));

        Assert.Single(history.List(caseId), e => e.Kind == CaseHistoryKind.ProcessRejected);
    }

    [Fact]
    public void OnCaseCreated_sets_a_non_default_version()
    {
        var caseId = Guid.NewGuid();
        var (_, views, _) = Setup(caseId);

        var view = views.Get(caseId)!;
        Assert.NotEqual(Guid.Empty, view.Version);
    }

    [Fact]
    public async Task HandleAsync_bumps_version_on_every_event()
    {
        var caseId = Guid.NewGuid();
        var (projector, views, _) = Setup(caseId);
        var v0 = views.Get(caseId)!.Version;

        await projector.HandleAsync(new TaskCreated(
            caseId.ToString(), "review", "Tham dinh", "anh", DateTimeOffset.UtcNow));
        var v1 = views.Get(caseId)!.Version;
        Assert.NotEqual(v0, v1);

        await projector.HandleAsync(new TaskCompleted(
            caseId.ToString(), "review", "Tham dinh", "anh", "OK", DateTimeOffset.UtcNow));
        var v2 = views.Get(caseId)!.Version;
        Assert.NotEqual(v1, v2);
    }

    [Fact]
    public async Task ProcessCancelled_clears_task_and_appends_history()
    {
        var caseId = Guid.NewGuid();
        var (projector, views, history) = Setup(caseId);

        await projector.HandleAsync(new ProcessCancelled(caseId.ToString(), DateTimeOffset.UtcNow));

        var view = views.Get(caseId)!;
        Assert.Equal("Da huy", view.WorkflowStatus);
        Assert.Null(view.CurrentTaskId);
        Assert.Single(history.List(caseId), e => e.Kind == CaseHistoryKind.ProcessCancelled);
    }
}
