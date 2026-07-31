using WorkflowPlatform.Workflow.Abstraction;
using WorkflowPlatform.Workflow.Abstraction.Contracts;

namespace WorkflowPlatform.Api.Infrastructure;

public sealed class ResilientProcessPort : IProcessPort
{
    private readonly IProcessPort _inner;
    private readonly ILogger<ResilientProcessPort> _logger;

    public ResilientProcessPort(IProcessPort inner, ILogger<ResilientProcessPort> logger)
    {
        _inner = inner;
        _logger = logger;
    }

    public Task DeployDefinitionAsync(CanonicalBpmn bpmn, CancellationToken ct)
        => _inner.DeployDefinitionAsync(bpmn, ct);

    public async Task<ProcessStartedAck> StartProcessAsync(StartProcessCommand command, CancellationToken ct)
    {
        try { return await _inner.StartProcessAsync(command, ct); }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Retrying StartProcess for {Key}", command.BusinessKey);
            await Task.Delay(100, ct);
            return await _inner.StartProcessAsync(command, ct);
        }
    }

    public async Task CompleteUserTaskAsync(CompleteTaskCommand command, CancellationToken ct)
    {
        try { await _inner.CompleteUserTaskAsync(command, ct); }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Retrying CompleteTask for {Key}", command.BusinessKey);
            await Task.Delay(100, ct);
            await _inner.CompleteUserTaskAsync(command, ct);
        }
    }

    public async Task CancelProcessAsync(string businessKey, CancellationToken ct)
    {
        try { await _inner.CancelProcessAsync(businessKey, ct); }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Retrying Cancel for {Key}", businessKey);
            await Task.Delay(100, ct);
            await _inner.CancelProcessAsync(businessKey, ct);
        }
    }

    public Task<ProcessStateView> GetProcessStateAsync(string businessKey, CancellationToken ct)
        => _inner.GetProcessStateAsync(businessKey, ct);
}
