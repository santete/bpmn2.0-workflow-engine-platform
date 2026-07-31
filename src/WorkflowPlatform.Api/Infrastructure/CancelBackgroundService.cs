using System.Threading.Channels;
using WorkflowPlatform.Workflow.Abstraction;

namespace WorkflowPlatform.Api.Infrastructure;

public sealed record CancelCommand(string BusinessKey);

public sealed class CancelBackgroundService : BackgroundService
{
    private readonly Channel<CancelCommand> _channel = Channel.CreateUnbounded<CancelCommand>();
    private readonly IServiceScopeFactory _scopeFactory;

    public CancelBackgroundService(IServiceScopeFactory scopeFactory)
        => _scopeFactory = scopeFactory;

    public ValueTask EnqueueAsync(CancelCommand cmd, CancellationToken ct = default)
        => _channel.Writer.WriteAsync(cmd, ct);

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await foreach (var cmd in _channel.Reader.ReadAllAsync(stoppingToken))
        {
            using var scope = _scopeFactory.CreateScope();
            var port = scope.ServiceProvider.GetRequiredService<IProcessPort>();
            try { await port.CancelProcessAsync(cmd.BusinessKey, stoppingToken); }
            catch { /* logged by exception handler; don't crash service */ }
        }
    }
}
