using System.Collections.Concurrent;
using WorkflowPlatform.Workflow.Abstraction;
using WorkflowPlatform.Workflow.Abstraction.Contracts;
using WorkflowPlatform.Workflow.Abstraction.Events;
using WorkflowPlatform.Workflow.Bpmn;

namespace WorkflowPlatform.Workflow.Adapter.Simple;

/// <summary>
/// Engine BPMN tối giản (MVP): thực thi quy trình tuyến tính từ BPMN 2.0 XML.
/// Lưu CHỈ trạng thái tiến trình + businessKey (correlation) — KHÔNG business data (điều kiện C2).
/// Đây là adapter thứ nhất; thêm adapter engine khác (Camunda/Flowable) không đụng domain (chứng minh tháo lắp).
/// </summary>
public sealed class SimpleBpmnEngineAdapter : IEngineAdapter
{
    private sealed class Instance
    {
        public required string BusinessKey { get; init; }
        public required string DefinitionKey { get; init; }
        public string? CurrentTaskId { get; set; }
        public ProcessStatus Status { get; set; } = ProcessStatus.Running;
    }

    private readonly ConcurrentDictionary<string, BpmnDefinition> _definitions = new();
    private readonly ConcurrentDictionary<string, Instance> _instances = new();

    public string EngineName => "simple-inmemory";

    private static WorkflowEvent Terminal(string businessKey, BpmnNode? end, DateTimeOffset now)
        => end is not null && end.Id.Contains("reject", StringComparison.OrdinalIgnoreCase)
            ? new ProcessRejected(businessKey, now)
            : new ProcessCompleted(businessKey, now);

    public void Deploy(CanonicalBpmn bpmn)
    {
        var def = BpmnParser.Parse(bpmn.Xml);
        _definitions[def.Key] = def;
    }

    public IReadOnlyList<WorkflowEvent> Start(StartProcessCommand command)
    {
        if (!_definitions.TryGetValue(command.ProcessDefinitionKey, out var def))
            throw new InvalidOperationException($"Chưa deploy định nghĩa '{command.ProcessDefinitionKey}'.");

        var now = DateTimeOffset.UtcNow;
        var events = new List<WorkflowEvent> { new ProcessStarted(command.BusinessKey, now) };

        var instance = new Instance { BusinessKey = command.BusinessKey, DefinitionKey = def.Key };
        _instances[command.BusinessKey] = instance;

        var firstStop = def.NextStop(def.StartNodeId);
        if (firstStop is { Kind: NodeKind.UserTask })
        {
            instance.CurrentTaskId = firstStop.Id;
            events.Add(new TaskCreated(command.BusinessKey, firstStop.Id, firstStop.Name, firstStop.Assignee, now));
        }
        else
        {
            instance.Status = ProcessStatus.Completed;
            events.Add(Terminal(command.BusinessKey, firstStop, now));
        }

        return events;
    }

    public IReadOnlyList<WorkflowEvent> CompleteTask(CompleteTaskCommand command)
    {
        if (!_instances.TryGetValue(command.BusinessKey, out var instance))
            throw new InvalidOperationException($"Không tìm thấy tiến trình cho '{command.BusinessKey}'.");
        if (instance.Status != ProcessStatus.Running)
            throw new InvalidOperationException("Tiến trình đã kết thúc.");
        if (instance.CurrentTaskId != command.TaskId)
            throw new InvalidOperationException(
                $"Task '{command.TaskId}' không phải task đang hoạt động ('{instance.CurrentTaskId}').");

        var def = _definitions[instance.DefinitionKey];
        var now = DateTimeOffset.UtcNow;
        var decision = command.Variables.TryGetValue("decision", out var dv) ? dv.Value : null;
        var taskName = def.Nodes.TryGetValue(command.TaskId, out var completedNode) ? completedNode.Name : command.TaskId;
        var events = new List<WorkflowEvent> { new TaskCompleted(command.BusinessKey, command.TaskId, taskName, command.Actor, decision, now) };

        var next = def.NextStop(command.TaskId, _ => decision);
        if (next is { Kind: NodeKind.UserTask })
        {
            instance.CurrentTaskId = next.Id;
            events.Add(new TaskCreated(command.BusinessKey, next.Id, next.Name, next.Assignee, now));
        }
        else
        {
            instance.CurrentTaskId = null;
            instance.Status = ProcessStatus.Completed;
            events.Add(Terminal(command.BusinessKey, next, now));
        }

        return events;
    }

    public ProcessStateView GetState(string businessKey)
    {
        if (!_instances.TryGetValue(businessKey, out var instance))
            return new ProcessStateView(businessKey, string.Empty, ProcessStatus.NotFound, Array.Empty<TaskView>());

        var def = _definitions[instance.DefinitionKey];
        var active = instance.CurrentTaskId is { } tid && def.Nodes.TryGetValue(tid, out var node)
            ? new[] { new TaskView(node.Id, node.Name) }
            : Array.Empty<TaskView>();

        return new ProcessStateView(businessKey, instance.DefinitionKey, instance.Status, active);
    }
}
