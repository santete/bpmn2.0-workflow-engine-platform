using System.Collections.Concurrent;
using WorkflowPlatform.Workflow.Abstraction;
using WorkflowPlatform.Workflow.Abstraction.Contracts;
using WorkflowPlatform.Workflow.Abstraction.Events;
using WorkflowPlatform.Workflow.Bpmn;

namespace WorkflowPlatform.Workflow.Adapter.Replay;

public sealed class ReplayEngineAdapter : IEngineAdapter
{
    private readonly ConcurrentDictionary<string, BpmnDefinition> _definitions = new();
    private readonly IReplayLogStore _log;

    public ReplayEngineAdapter(IReplayLogStore log) => _log = log;

    public string EngineName => "replay-recompute";

    public void Deploy(CanonicalBpmn bpmn)
    {
        var def = BpmnParser.Parse(bpmn.Xml);
        _definitions[def.Key] = def;
    }

    public IReadOnlyList<WorkflowEvent> Start(StartProcessCommand command)
    {
        if (!_definitions.TryGetValue(command.ProcessDefinitionKey, out var def))
            throw new InvalidOperationException($"Chưa deploy định nghĩa '{command.ProcessDefinitionKey}'.");

        _log.EnsureInstance(command.BusinessKey, def.Key);

        var now = DateTimeOffset.UtcNow;
        var (status, activeNodes) = Compute(def, _log.GetCompletions(command.BusinessKey));
        var events = new List<WorkflowEvent> { new ProcessStarted(command.BusinessKey, now) };

        if (status == ProcessStatus.Running)
        {
            foreach (var node in activeNodes)
                events.Add(new TaskCreated(command.BusinessKey, node.Id, node.Name, node.Assignee, now));
        }
        else
        {
            events.Add(ToTerminal(command.BusinessKey, status, activeNodes.Any() ? activeNodes[0] : null, now));
        }

        return events;
    }

    public IReadOnlyList<WorkflowEvent> CompleteTask(CompleteTaskCommand command)
    {
        var defKey = _log.GetDefinitionKey(command.BusinessKey)
            ?? throw new InvalidOperationException($"Không tìm thấy tiến trình cho '{command.BusinessKey}'.");
        var def = _definitions[defKey];

        var (status, activeNodes) = Compute(def, _log.GetCompletions(command.BusinessKey));
        if (status != ProcessStatus.Running)
            throw new InvalidOperationException("Tiến trình đã kết thúc.");
        if (!activeNodes.Any(n => n.Id == command.TaskId))
            throw new InvalidOperationException(
                $"Task '{command.TaskId}' không phải task đang hoạt động.");

        var decision = command.Variables.TryGetValue("decision", out var dv) ? dv.Value : null;
        _log.Append(command.BusinessKey, command.TaskId, decision);

        var completedNode = def.Nodes[command.TaskId];
        var now = DateTimeOffset.UtcNow;
        var (nextStatus, nextNodes) = Compute(def, _log.GetCompletions(command.BusinessKey));
        var events = new List<WorkflowEvent>
        {
            new TaskCompleted(command.BusinessKey, command.TaskId, completedNode.Name, command.Actor, decision, now)
        };

        if (nextStatus == ProcessStatus.Running)
        {
            // Chỉ emit TaskCreated cho các node MỚI (chưa có trước đó)
            var newIds = nextNodes.Select(n => n.Id).Except(activeNodes.Select(n => n.Id)).ToList();
            foreach (var id in newIds)
            {
                var node = def.Nodes[id];
                events.Add(new TaskCreated(command.BusinessKey, node.Id, node.Name, node.Assignee, now));
            }
        }
        else
        {
            events.Add(ToTerminal(command.BusinessKey, nextStatus, nextNodes.Any() ? nextNodes[0] : null, now));
        }

        return events;
    }

    public IReadOnlyList<WorkflowEvent> Cancel(string businessKey)
    {
        var defKey = _log.GetDefinitionKey(businessKey)
            ?? throw new InvalidOperationException($"Không tìm thấy tiến trình cho '{businessKey}'.");
        if (_log.IsCancelled(businessKey))
            throw new InvalidOperationException("Tiến trình đã kết thúc.");

        var def = _definitions[defKey];
        var (status, _) = Compute(def, _log.GetCompletions(businessKey));
        if (status != ProcessStatus.Running)
            throw new InvalidOperationException("Tiến trình đã kết thúc.");

        _log.Cancel(businessKey);
        return new List<WorkflowEvent> { new ProcessCancelled(businessKey, DateTimeOffset.UtcNow) };
    }

    public ProcessStateView GetState(string businessKey)
    {
        var defKey = _log.GetDefinitionKey(businessKey);
        if (defKey is null)
            return new ProcessStateView(businessKey, string.Empty, ProcessStatus.NotFound, Array.Empty<TaskView>());

        if (_log.IsCancelled(businessKey))
            return new ProcessStateView(businessKey, defKey, ProcessStatus.Cancelled, Array.Empty<TaskView>());

        var def = _definitions[defKey];
        var (status, current) = Compute(def, _log.GetCompletions(businessKey));
        var active = status == ProcessStatus.Running
            ? current.Select(n => new TaskView(n.Id, n.Name)).ToList()
            : new List<TaskView>();
        return new ProcessStateView(businessKey, defKey, status, active);
    }

    private static WorkflowEvent ToTerminal(string businessKey, ProcessStatus status, BpmnNode? node, DateTimeOffset now)
    {
        if (status == ProcessStatus.Completed)
            return node is not null && node.Id.Contains("reject", StringComparison.OrdinalIgnoreCase)
                ? new ProcessRejected(businessKey, now)
                : new ProcessCompleted(businessKey, now);
        throw new InvalidOperationException($"Unexpected status for terminal: {status}");
    }

    private static (ProcessStatus, List<BpmnNode>) Compute(BpmnDefinition def, IReadOnlyList<CompletionEntry> completions)
    {
        var first = def.NextStop(def.StartNodeId);
        if (first is null)
            return (ProcessStatus.Completed, new List<BpmnNode>());

        // Parallel fork
        if (first.Kind == NodeKind.ParallelGateway)
        {
            var branches = def.NextStops(first.Id);
            var activeTasks = new List<BpmnNode>();
            foreach (var b in branches)
            {
                var done = completions.Any(c => c.TaskId == b.Id);
                if (!done)
                    activeTasks.Add(b);
            }

            if (activeTasks.Count > 0)
                return (ProcessStatus.Running, activeTasks);

            // All completed → join
            var afterJoin = def.NextStop(first.Id); // qua join gateway → next
            // walk past join
            var joinNodeId = def.Outgoing(branches[0].Id).Select(f => f.TargetRef).FirstOrDefault() ?? "";
            afterJoin = def.NextStop(joinNodeId);
            if (afterJoin is { Kind: NodeKind.UserTask })
                return (ProcessStatus.Running, new List<BpmnNode> { afterJoin });
            return (ProcessStatus.Completed, afterJoin is not null ? new List<BpmnNode> { afterJoin } : new());
        }

        // Sequential
        return ComputeLinear(def, completions, first);
    }

    private static (ProcessStatus, List<BpmnNode>) ComputeLinear(BpmnDefinition def, IReadOnlyList<CompletionEntry> completions, BpmnNode start)
    {
        var stop = start;
        var i = 0;
        while (stop is { Kind: NodeKind.UserTask })
        {
            if (i < completions.Count && completions[i].TaskId == stop.Id)
            {
                var decision = completions[i].Decision;
                i++;
                stop = def.NextStop(stop.Id, _ => decision);
            }
            else
            {
                return (ProcessStatus.Running, new List<BpmnNode> { stop });
            }
        }
        return (ProcessStatus.Completed, stop is not null ? new List<BpmnNode> { stop } : new());
    }
}
