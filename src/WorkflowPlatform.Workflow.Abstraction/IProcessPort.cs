using WorkflowPlatform.Workflow.Abstraction.Contracts;

namespace WorkflowPlatform.Workflow.Abstraction;

/// <summary>
/// Driving port — hợp đồng DUY NHẤT mà domain (PH-4) thấy. Domain không biết engine nào phía sau.
/// </summary>
public interface IProcessPort
{
    Task DeployDefinitionAsync(CanonicalBpmn bpmn, CancellationToken ct = default);
    Task<ProcessStartedAck> StartProcessAsync(StartProcessCommand command, CancellationToken ct = default);
    Task CompleteUserTaskAsync(CompleteTaskCommand command, CancellationToken ct = default);
    Task<ProcessStateView> GetProcessStateAsync(string businessKey, CancellationToken ct = default);
}
