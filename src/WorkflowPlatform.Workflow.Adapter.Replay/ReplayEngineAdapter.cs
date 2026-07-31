using System.Collections.Concurrent;
using WorkflowPlatform.Workflow.Abstraction;
using WorkflowPlatform.Workflow.Abstraction.Contracts;
using WorkflowPlatform.Workflow.Abstraction.Events;
using WorkflowPlatform.Workflow.Bpmn;

namespace WorkflowPlatform.Workflow.Adapter.Replay;

/// <summary>
/// Engine #2 — mô hình KHÁC HẲN Simple: KHÔNG lưu con trỏ hiện tại. Chỉ lưu NHẬT KÝ hoàn thành task
/// (qua <see cref="IReplayLogStore"/>), rồi TÍNH LẠI vị trí bằng cách replay BPMN mỗi lần.
/// Nhật ký có thể persist (EF) → tiến trình sống sót qua restart. Cùng hợp đồng <see cref="IEngineAdapter"/>.
/// </summary>
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
        var (status, current) = Compute(def, _log.GetCompletions(command.BusinessKey));
        return new List<WorkflowEvent>
        {
            new ProcessStarted(command.BusinessKey, now),
            ToTerminalOrTask(command.BusinessKey, status, current, now)
        };
    }

    public IReadOnlyList<WorkflowEvent> CompleteTask(CompleteTaskCommand command)
    {
        var defKey = _log.GetDefinitionKey(command.BusinessKey)
            ?? throw new InvalidOperationException($"Không tìm thấy tiến trình cho '{command.BusinessKey}'.");
        var def = _definitions[defKey];

        var (status, current) = Compute(def, _log.GetCompletions(command.BusinessKey));
        if (status != ProcessStatus.Running)
            throw new InvalidOperationException("Tiến trình đã kết thúc.");
        if (current!.Id != command.TaskId)
            throw new InvalidOperationException(
                $"Task '{command.TaskId}' không phải task đang hoạt động ('{current.Id}').");

        var decision = command.Variables.TryGetValue("decision", out var dv) ? dv.Value : null;
        _log.Append(command.BusinessKey, command.TaskId, decision);

        var now = DateTimeOffset.UtcNow;
        var (next, nextTask) = Compute(def, _log.GetCompletions(command.BusinessKey));
        return new List<WorkflowEvent>
        {
            new TaskCompleted(command.BusinessKey, command.TaskId, current.Name, command.Actor, decision, now),
            ToTerminalOrTask(command.BusinessKey, next, nextTask, now)
        };
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
        var active = status == ProcessStatus.Running && current is not null
            ? new[] { new TaskView(current.Id, current.Name) }
            : Array.Empty<TaskView>();
        return new ProcessStateView(businessKey, defKey, status, active);
    }

    private static WorkflowEvent ToTerminalOrTask(string businessKey, ProcessStatus status, BpmnNode? node, DateTimeOffset now)
    {
        if (status != ProcessStatus.Completed)
            return new TaskCreated(businessKey, node!.Id, node.Name, node.Assignee, now);

        return node is not null && node.Id.Contains("reject", StringComparison.OrdinalIgnoreCase)
            ? new ProcessRejected(businessKey, now)
            : new ProcessCompleted(businessKey, now);
    }

    /// <summary>Recompute thuần từ nhật ký: user task chưa hoàn thành đầu tiên = đang hoạt động; gateway giải bằng decision.</summary>
    private static (ProcessStatus, BpmnNode?) Compute(BpmnDefinition def, IReadOnlyList<CompletionEntry> completions)
    {
        var stop = def.NextStop(def.StartNodeId);
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
                return (ProcessStatus.Running, stop);
            }
        }
        return (ProcessStatus.Completed, stop); // stop = nút End (dùng để phân biệt reject/complete)
    }
}
