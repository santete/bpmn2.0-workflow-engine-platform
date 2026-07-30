using WorkflowPlatform.Workflow.Abstraction.Events;

namespace WorkflowPlatform.Workflow.Abstraction;

/// <summary>Bên tiêu thụ sự kiện tiến trình (vd projector read model, domain reactor).</summary>
public interface IWorkflowEventHandler
{
    Task HandleAsync(WorkflowEvent evt, CancellationToken ct = default);
}

/// <summary>Kênh phát sự kiện tiến trình ra ngoài (bể sự kiện PH-6). Tách WorkflowService khỏi hạ tầng bus.</summary>
public interface IWorkflowEventPublisher
{
    Task PublishAsync(WorkflowEvent evt, CancellationToken ct = default);
}
