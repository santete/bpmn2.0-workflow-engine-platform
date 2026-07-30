using WorkflowPlatform.Workflow.Abstraction;
using WorkflowPlatform.Workflow.Abstraction.Contracts;
using WorkflowPlatform.Workflow.Abstraction.Events;
using WorkflowPlatform.Workflow.Adapter.Simple;
using Xunit;

namespace WorkflowPlatform.Tests;

public class WorkflowServiceTests
{
    private sealed class CapturingPublisher : IWorkflowEventPublisher
    {
        public List<WorkflowEvent> Events { get; } = new();
        public Task PublishAsync(WorkflowEvent evt, CancellationToken ct = default)
        {
            Events.Add(evt);
            return Task.CompletedTask;
        }
    }

    [Fact]
    public async Task Port_publishes_engine_events_to_bus()
    {
        var engine = new SimpleBpmnEngineAdapter();
        var publisher = new CapturingPublisher();
        var port = new WorkflowService(engine, publisher);
        await port.DeployDefinitionAsync(new CanonicalBpmn("case-approval", TestBpmn.CaseApproval));

        var ack = await port.StartProcessAsync(new StartProcessCommand(
            "case-approval", "CASE-9", new Dictionary<string, ProcessVariable>(), "tester"));

        Assert.Equal("CASE-9", ack.BusinessKey);
        Assert.Contains(publisher.Events, e => e is ProcessStarted);
        Assert.Contains(publisher.Events, e => e is TaskCreated { TaskId: "review" });
    }
}
