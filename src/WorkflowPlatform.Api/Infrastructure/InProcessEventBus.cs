using WorkflowPlatform.Workflow.Abstraction;
using WorkflowPlatform.Workflow.Abstraction.Events;

namespace WorkflowPlatform.Api.Infrastructure;

/// <summary>
/// Bể sự kiện in-process (MVP thay cho message broker PH-6). Đẩy WorkflowEvent tới mọi handler đã đăng ký —
/// domain ↔ workflow tách rời qua đây, không call trực tiếp.
/// </summary>
public sealed class InProcessEventBus : IWorkflowEventPublisher
{
    private readonly IEnumerable<IWorkflowEventHandler> _handlers;

    public InProcessEventBus(IEnumerable<IWorkflowEventHandler> handlers) => _handlers = handlers;

    public async Task PublishAsync(WorkflowEvent evt, CancellationToken ct = default)
    {
        foreach (var handler in _handlers)
            await handler.HandleAsync(evt, ct);
    }
}
