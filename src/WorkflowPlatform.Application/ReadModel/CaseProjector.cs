using WorkflowPlatform.Domain.Cases;
using WorkflowPlatform.Workflow.Abstraction;
using WorkflowPlatform.Workflow.Abstraction.Events;

namespace WorkflowPlatform.Application.ReadModel;

/// <summary>
/// Projector GENERIC: dựng read model từ sự kiện tiến trình cho BẤT KỲ quy trình nào (không gắn cứng
/// tên bước). WorkflowStatus = tên task đang mở; đồng bộ trạng thái nghiệp vụ của domain qua event.
/// </summary>
public sealed class CaseProjector : IWorkflowEventHandler
{
    private readonly ICaseReadStore _store;
    private readonly ICaseRepository _repository;
    private readonly ICaseHistoryStore _history;

    public CaseProjector(ICaseReadStore store, ICaseRepository repository, ICaseHistoryStore history)
    {
        _store = store;
        _repository = repository;
        _history = history;
    }

    public void OnCaseCreated(Guid caseId, string title, string definitionKey)
        => _store.Upsert(new CaseView
        {
            Id = caseId, Title = title, DefinitionKey = definitionKey,
            BusinessStatus = "Draft", WorkflowStatus = "Khoi tao"
        });

    public Task HandleAsync(WorkflowEvent evt, CancellationToken ct = default)
    {
        if (!Guid.TryParse(evt.BusinessKey, out var caseId)) return Task.CompletedTask;
        var view = _store.Get(caseId);
        if (view is null) return Task.CompletedTask;

        switch (evt)
        {
            case ProcessStarted:
                view.WorkflowStatus = "Dang xu ly";
                break;

            case TaskCreated created:
                view.CurrentTaskId = created.TaskId;
                view.CurrentTaskName = created.TaskName;
                view.CurrentTaskAssignee = created.Assignee;
                view.WorkflowStatus = created.TaskName;   // hiển thị tên bước động
                if (view.BusinessStatus is "Draft")
                {
                    var @case = _repository.Get(caseId);
                    if (@case is not null) { @case.MarkInReview(); _repository.Save(@case); }
                    view.BusinessStatus = "InReview";
                }
                break;

            case TaskCompleted completed:
                _history.Append(new CaseHistoryEntry(
                    caseId, CaseHistoryKind.TaskCompleted,
                    completed.TaskId, completed.TaskName, completed.Actor, completed.Decision,
                    completed.OccurredAt));
                break;

            case ProcessRejected rejected:
                view.CurrentTaskId = null;
                view.CurrentTaskName = null;
                view.CurrentTaskAssignee = null;
                view.WorkflowStatus = "Tu choi";
                _history.Append(new CaseHistoryEntry(
                    caseId, CaseHistoryKind.ProcessRejected, null, null, null, null, rejected.OccurredAt));
                {
                    var @case = _repository.Get(caseId);
                    if (@case is not null) { @case.Reject(); _repository.Save(@case); }
                    view.BusinessStatus = "Rejected";
                }
                break;

            case ProcessCompleted done:
                view.CurrentTaskId = null;
                view.CurrentTaskName = null;
                view.CurrentTaskAssignee = null;
                view.WorkflowStatus = "Hoan tat";
                _history.Append(new CaseHistoryEntry(
                    caseId, CaseHistoryKind.ProcessCompleted, null, null, null, null, done.OccurredAt));
                {
                    var @case = _repository.Get(caseId);
                    if (@case is not null) { @case.Approve(); _repository.Save(@case); }
                    view.BusinessStatus = "Approved";
                }
                break;
        }

        _store.Upsert(view);
        return Task.CompletedTask;
    }
}
