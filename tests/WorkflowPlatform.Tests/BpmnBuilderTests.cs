using WorkflowPlatform.Workflow.Abstraction.Contracts;
using WorkflowPlatform.Workflow.Abstraction.Events;
using WorkflowPlatform.Workflow.Adapter.Simple;
using WorkflowPlatform.Workflow.Bpmn;
using Xunit;

namespace WorkflowPlatform.Tests;

/// <summary>Quy trình sinh động từ BpmnBuilder chạy được ngay trên engine (không sửa code engine).</summary>
public class BpmnBuilderTests
{
    private static SimpleBpmnEngineAdapter Deploy(string xml)
    {
        var e = new SimpleBpmnEngineAdapter();
        e.Deploy(new CanonicalBpmn("t", xml));
        return e;
    }
    private static StartProcessCommand Start(string k) => new("t", k, new Dictionary<string, ProcessVariable>(), "x");
    private static CompleteTaskCommand Done(string k, string t, string? d = null)
        => new(k, t, d is null ? new() : new Dictionary<string, ProcessVariable> { ["decision"] = ProcessVariable.Enum(d) }, "x");

    [Fact]
    public void Linear_built_process_runs_to_completion()
    {
        var xml = BpmnBuilder.Build("t", "Test", new List<(string, string, string?)> { ("a", "A", null), ("b", "B", null) }, endsWithDecision: false);
        var e = Deploy(xml);

        Assert.Equal("a", Assert.IsType<TaskCreated>(e.Start(Start("K1"))[1]).TaskId);
        Assert.Equal("b", Assert.IsType<TaskCreated>(e.CompleteTask(Done("K1", "a"))[1]).TaskId);
        Assert.Contains(e.CompleteTask(Done("K1", "b")), x => x is ProcessCompleted);
    }

    [Fact]
    public void Built_process_with_decision_supports_reject()
    {
        var xml = BpmnBuilder.Build("t", "Test", new List<(string, string, string?)> { ("a", "A", null) }, endsWithDecision: true);
        var e = Deploy(xml);
        e.Start(Start("K2"));

        Assert.Contains(e.CompleteTask(Done("K2", "a", "REJECTED")), x => x is ProcessRejected);
    }

    [Fact]
    public void Builder_emits_assignee_and_parser_reads_it_back()
    {
        var xml = BpmnBuilder.Build("t", "Test",
            new List<(string, string, string?)> { ("a", "A", "an.nguyen"), ("b", "B", null) },
            endsWithDecision: false);

        var def = BpmnParser.Parse(xml);

        Assert.Equal("an.nguyen", def.Nodes["a"].Assignee);
        Assert.Null(def.Nodes["b"].Assignee);
    }
}
