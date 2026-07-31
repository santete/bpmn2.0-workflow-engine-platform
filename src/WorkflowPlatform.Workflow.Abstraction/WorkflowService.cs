using WorkflowPlatform.Workflow.Abstraction.Contracts;

namespace WorkflowPlatform.Workflow.Abstraction;

/// <summary>
/// Hiện thực IProcessPort: cầu nối giữa domain và engine. Nhận sự kiện canonical do adapter phát,
/// đẩy ra event publisher (PH-6). Engine KHÔNG nằm trên đường request đồng bộ nóng (giải X6):
/// port chỉ ack, kết quả về domain qua event.
/// </summary>
public sealed class WorkflowService : IProcessPort
{
    private readonly IEngineAdapter _engine;
    private readonly IWorkflowEventPublisher _publisher;

    public WorkflowService(IEngineAdapter engine, IWorkflowEventPublisher publisher)
    {
        _engine = engine;
        _publisher = publisher;
    }

    public Task DeployDefinitionAsync(CanonicalBpmn bpmn, CancellationToken ct = default)
    {
        _engine.Deploy(bpmn);
        return Task.CompletedTask;
    }

    public async Task<ProcessStartedAck> StartProcessAsync(StartProcessCommand command, CancellationToken ct = default)
    {
        var events = _engine.Start(command);
        foreach (var evt in events)
            await _publisher.PublishAsync(evt, ct);

        return new ProcessStartedAck(command.BusinessKey, command.BusinessKey);
    }

    public async Task CompleteUserTaskAsync(CompleteTaskCommand command, CancellationToken ct = default)
    {
        var events = _engine.CompleteTask(command);
        foreach (var evt in events)
            await _publisher.PublishAsync(evt, ct);
    }

    public async Task CancelProcessAsync(string businessKey, CancellationToken ct = default)
    {
        var events = _engine.Cancel(businessKey);
        foreach (var evt in events)
            await _publisher.PublishAsync(evt, ct);
    }

    public Task<ProcessStateView> GetProcessStateAsync(string businessKey, CancellationToken ct = default)
        => Task.FromResult(_engine.GetState(businessKey));
}
