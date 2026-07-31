using System.Collections.Concurrent;
using WorkflowPlatform.Workflow.Abstraction;
using WorkflowPlatform.Workflow.Abstraction.Contracts;
using WorkflowPlatform.Workflow.Abstraction.Events;
using WorkflowPlatform.Workflow.Bpmn;

namespace WorkflowPlatform.Workflow.Adapter.Simple;

public sealed class SimpleBpmnEngineAdapter : IEngineAdapter
{
    private sealed class Instance
    {
        public required string BusinessKey { get; init; }
        public required string DefinitionKey { get; init; }
        public HashSet<string> CurrentTaskIds { get; } = new();
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
        if (firstStop is { Kind: NodeKind.ParallelGateway })
        {
            var parallel = def.NextStops(firstStop.Id);
            foreach (var t in parallel)
            {
                instance.CurrentTaskIds.Add(t.Id);
                events.Add(new TaskCreated(command.BusinessKey, t.Id, t.Name, t.Assignee, now));
            }
        }
        else if (firstStop is { Kind: NodeKind.UserTask })
        {
            instance.CurrentTaskIds.Add(firstStop.Id);
            events.Add(new TaskCreated(command.BusinessKey, firstStop.Id, firstStop.Name, firstStop.Assignee, now));
        }
        else
        {
            instance.Status = ProcessStatus.Completed;
            events.Add(Terminal(command.BusinessKey, firstStop, now));
        }

        return events;
    }

    public IReadOnlyList<WorkflowEvent> Cancel(string businessKey)
    {
        if (!_instances.TryGetValue(businessKey, out var instance))
            throw new InvalidOperationException($"Không tìm thấy tiến trình cho '{businessKey}'.");
        if (instance.Status != ProcessStatus.Running)
            throw new InvalidOperationException("Tiến trình đã kết thúc.");

        instance.Status = ProcessStatus.Cancelled;
        instance.CurrentTaskIds.Clear();
        return new List<WorkflowEvent> { new ProcessCancelled(businessKey, DateTimeOffset.UtcNow) };
    }

    public IReadOnlyList<WorkflowEvent> CompleteTask(CompleteTaskCommand command)
    {
        if (!_instances.TryGetValue(command.BusinessKey, out var instance))
            throw new InvalidOperationException($"Không tìm thấy tiến trình cho '{command.BusinessKey}'.");
        if (instance.Status != ProcessStatus.Running)
            throw new InvalidOperationException("Tiến trình đã kết thúc.");
        if (!instance.CurrentTaskIds.Contains(command.TaskId))
            throw new InvalidOperationException(
                $"Task '{command.TaskId}' không phải task đang hoạt động.");

        var def = _definitions[instance.DefinitionKey];
        var now = DateTimeOffset.UtcNow;
        var decision = command.Variables.TryGetValue("decision", out var dv) ? dv.Value : null;
        var taskName = def.Nodes.TryGetValue(command.TaskId, out var completedNode) ? completedNode.Name : command.TaskId;
        var events = new List<WorkflowEvent> { new TaskCompleted(command.BusinessKey, command.TaskId, taskName, command.Actor, decision, now) };

        instance.CurrentTaskIds.Remove(command.TaskId);

        // Kiểm tra xem node vừa complete có nối vào join gateway không
        var next = def.NextStop(command.TaskId, _ => decision);
        bool directToJoin = next is { Kind: NodeKind.ParallelGateway };

        if (instance.CurrentTaskIds.Count > 0)
        {
            // Còn task song song — chỉ báo completed, không advance
            return events;
        }

        // Tất cả task song song đã xong → join → advance
        if (directToJoin)
        {
            var afterJoin = def.NextStop(next!.Id);
            if (afterJoin is { Kind: NodeKind.UserTask })
            {
                instance.CurrentTaskIds.Add(afterJoin.Id);
                events.Add(new TaskCreated(command.BusinessKey, afterJoin.Id, afterJoin.Name, afterJoin.Assignee, now));
            }
            else
            {
                instance.Status = ProcessStatus.Completed;
                events.Add(Terminal(command.BusinessKey, afterJoin, now));
            }
        }
        else
        {
            // Luồng tuần tự — như cũ
            if (next is { Kind: NodeKind.UserTask })
            {
                instance.CurrentTaskIds.Add(next.Id);
                events.Add(new TaskCreated(command.BusinessKey, next.Id, next.Name, next.Assignee, now));
            }
            else
            {
                instance.Status = ProcessStatus.Completed;
                events.Add(Terminal(command.BusinessKey, next, now));
            }
        }

        return events;
    }

    public ProcessStateView GetState(string businessKey)
    {
        if (!_instances.TryGetValue(businessKey, out var instance))
            return new ProcessStateView(businessKey, string.Empty, ProcessStatus.NotFound, Array.Empty<TaskView>());

        var def = _definitions[instance.DefinitionKey];
        var active = instance.CurrentTaskIds
            .Select(tid => def.Nodes.TryGetValue(tid, out var n) ? new TaskView(n.Id, n.Name) : null)
            .Where(v => v is not null)
            .Select(v => v!)
            .ToList();

        return new ProcessStateView(businessKey, instance.DefinitionKey, instance.Status, active);
    }
}
