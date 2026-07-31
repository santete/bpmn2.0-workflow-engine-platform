using WorkflowPlatform.Workflow.Abstraction;
using WorkflowPlatform.Workflow.Abstraction.Contracts;
using WorkflowPlatform.Workflow.Abstraction.Events;
using Xunit;

namespace WorkflowPlatform.Tests;

/// <summary>
/// FIT-010 (engine-swap): hợp đồng mọi <see cref="IEngineAdapter"/> phải thỏa. Chạy trên ≥2 engine
/// (Simple stored-cursor + Replay recompute) → cả hai xanh = kiến trúc tháo lắp được, không phải lời hứa.
/// </summary>
public abstract class EngineContractTestsBase
{
    protected abstract IEngineAdapter CreateEngine();

    private IEngineAdapter Deployed()
    {
        var engine = CreateEngine();
        engine.Deploy(new CanonicalBpmn("case-approval", TestBpmn.CaseApproval));
        return engine;
    }

    private static StartProcessCommand Start(string key)
        => new("case-approval", key, new Dictionary<string, ProcessVariable>(), "t");

    private static CompleteTaskCommand Complete(string key, string task)
        => new(key, task, new Dictionary<string, ProcessVariable>(), "t");

    [Fact]
    public void Start_emits_started_then_first_user_task()
    {
        var engine = Deployed();
        var events = engine.Start(Start("A"));
        Assert.Collection(events,
            e => Assert.IsType<ProcessStarted>(e),
            e => Assert.Equal("review", Assert.IsType<TaskCreated>(e).TaskId));
    }

    [Fact]
    public void Completing_review_advances_to_approve()
    {
        var engine = Deployed();
        engine.Start(Start("B"));
        var events = engine.CompleteTask(Complete("B", "review"));
        Assert.Collection(events,
            e => Assert.Equal("review", Assert.IsType<TaskCompleted>(e).TaskId),
            e => Assert.Equal("approve", Assert.IsType<TaskCreated>(e).TaskId));
    }

    [Fact]
    public void Completing_approve_completes_process()
    {
        var engine = Deployed();
        engine.Start(Start("C"));
        engine.CompleteTask(Complete("C", "review"));
        var events = engine.CompleteTask(Complete("C", "approve"));
        Assert.Contains(events, e => e is ProcessCompleted);
        Assert.Equal(ProcessStatus.Completed, engine.GetState("C").Status);
    }

    [Fact]
    public void Rejecting_at_approve_ends_process_via_reject_branch()
    {
        var engine = Deployed();
        engine.Start(Start("F"));
        engine.CompleteTask(Complete("F", "review"));

        var reject = new CompleteTaskCommand("F", "approve",
            new Dictionary<string, ProcessVariable> { ["decision"] = ProcessVariable.Enum("REJECTED") }, "t");
        var events = engine.CompleteTask(reject);

        Assert.Contains(events, e => e is ProcessRejected);
        Assert.DoesNotContain(events, e => e is ProcessCompleted);
        Assert.Equal(ProcessStatus.Completed, engine.GetState("F").Status);
    }

    [Fact]
    public void Completing_wrong_task_is_rejected()
    {
        var engine = Deployed();
        engine.Start(Start("D"));
        Assert.Throws<InvalidOperationException>(() => engine.CompleteTask(Complete("D", "approve")));
    }

    [Fact]
    public void TaskCreated_carries_assignee_from_definition()
    {
        var engine = Deployed();
        var events = engine.Start(Start("G"));
        var created = Assert.IsType<TaskCreated>(events[1]);
        Assert.Equal("review", created.TaskId);
        Assert.Equal("thamdinh", created.Assignee);
    }

    [Fact]
    public void TaskCompleted_carries_actor_decision_and_task_name()
    {
        var engine = Deployed();
        engine.Start(Start("H"));
        var cmd = new CompleteTaskCommand("H", "approve",
            new Dictionary<string, ProcessVariable> { ["decision"] = ProcessVariable.Enum("REJECTED") },
            "lanhdao01");
        engine.CompleteTask(Complete("H", "review"));
        var events = engine.CompleteTask(cmd);

        var completed = Assert.IsType<TaskCompleted>(events[0]);
        Assert.Equal("approve", completed.TaskId);
        Assert.Equal("Phe duyet", completed.TaskName);
        Assert.Equal("lanhdao01", completed.Actor);
        Assert.Equal("REJECTED", completed.Decision);
    }

    [Fact]
    public void GetState_reports_active_task_while_running()
    {
        var engine = Deployed();
        engine.Start(Start("E"));
        var state = engine.GetState("E");
        Assert.Equal(ProcessStatus.Running, state.Status);
        Assert.Equal("review", Assert.Single(state.ActiveTasks).TaskId);
    }

    [Fact]
    public void Cancel_ends_running_process_with_cancelled_event_and_state()
    {
        var engine = Deployed();
        engine.Start(Start("I"));
        var events = engine.Cancel("I");

        Assert.Contains(events, e => e is ProcessCancelled);
        Assert.Equal(ProcessStatus.Cancelled, engine.GetState("I").Status);
    }

    [Fact]
    public void Cancel_on_already_ended_process_is_rejected()
    {
        var engine = Deployed();
        engine.Start(Start("J"));
        engine.Cancel("J");
        Assert.Throws<InvalidOperationException>(() => engine.Cancel("J"));
    }
}

public abstract class ParallelEngineContractTestsBase
{
    protected abstract IEngineAdapter CreateEngine();

    private IEngineAdapter Deployed()
    {
        var engine = CreateEngine();
        engine.Deploy(new CanonicalBpmn("parallel", TestBpmn.ParallelFork));
        return engine;
    }

    [Fact]
    public void Fork_creates_two_active_tasks()
    {
        var engine = Deployed();
        var events = engine.Start(new StartProcessCommand("parallel", "P1",
            new Dictionary<string, ProcessVariable>(), "x"));
        var created = events.OfType<TaskCreated>().ToList();
        Assert.Equal(2, created.Count);
        Assert.Contains(created, c => c.TaskId == "taskA");
        Assert.Contains(created, c => c.TaskId == "taskB");
    }

    [Fact]
    public void Completing_one_forked_task_leaves_other_running()
    {
        var engine = Deployed();
        engine.Start(new StartProcessCommand("parallel", "P2",
            new Dictionary<string, ProcessVariable>(), "x"));

        var events = engine.CompleteTask(new CompleteTaskCommand("P2", "taskA",
            new Dictionary<string, ProcessVariable>(), "a"));
        Assert.Single(events.OfType<TaskCompleted>());
        Assert.DoesNotContain(events, e => e is TaskCreated);
        Assert.Equal(ProcessStatus.Running, engine.GetState("P2").Status);
    }

    [Fact]
    public void Completing_all_tasks_joins_and_ends()
    {
        var engine = Deployed();
        engine.Start(new StartProcessCommand("parallel", "P3",
            new Dictionary<string, ProcessVariable>(), "x"));
        engine.CompleteTask(new CompleteTaskCommand("P3", "taskA",
            new Dictionary<string, ProcessVariable>(), "a"));

        var events = engine.CompleteTask(new CompleteTaskCommand("P3", "taskB",
            new Dictionary<string, ProcessVariable>(), "b"));
        Assert.Contains(events, e => e is ProcessCompleted);
        Assert.Equal(ProcessStatus.Completed, engine.GetState("P3").Status);
    }
}

public sealed class SimpleEngineContractTests : EngineContractTestsBase
{
    protected override IEngineAdapter CreateEngine()
        => new WorkflowPlatform.Workflow.Adapter.Simple.SimpleBpmnEngineAdapter();
}

public sealed class ReplayEngineContractTests : EngineContractTestsBase
{
    protected override IEngineAdapter CreateEngine()
        => new WorkflowPlatform.Workflow.Adapter.Replay.ReplayEngineAdapter(
            new WorkflowPlatform.Workflow.Adapter.Replay.InMemoryReplayLogStore());
}

public sealed class SimpleParallelEngineContractTests : ParallelEngineContractTestsBase
{
    protected override IEngineAdapter CreateEngine()
        => new WorkflowPlatform.Workflow.Adapter.Simple.SimpleBpmnEngineAdapter();
}

public sealed class ReplayParallelEngineContractTests : ParallelEngineContractTestsBase
{
    protected override IEngineAdapter CreateEngine()
        => new WorkflowPlatform.Workflow.Adapter.Replay.ReplayEngineAdapter(
            new WorkflowPlatform.Workflow.Adapter.Replay.InMemoryReplayLogStore());
}
