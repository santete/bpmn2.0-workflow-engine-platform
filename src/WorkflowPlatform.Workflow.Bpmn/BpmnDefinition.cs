namespace WorkflowPlatform.Workflow.Bpmn;

public enum NodeKind { Start, UserTask, Gateway, End }

public sealed record BpmnNode(string Id, string Name, NodeKind Kind);

/// <summary>Một luồng nối có thể mang điều kiện (dùng cho exclusiveGateway).</summary>
public sealed record BpmnFlow(string Id, string SourceRef, string TargetRef, string? ConditionName, string? ConditionValue);

/// <summary>Định nghĩa BPMN đã parse: nút + luồng nối (adjacency).</summary>
public sealed class BpmnDefinition
{
    public required string Key { get; init; }
    public required string Name { get; init; }
    public required string StartNodeId { get; init; }
    public required IReadOnlyDictionary<string, BpmnNode> Nodes { get; init; }
    public required IReadOnlyList<BpmnFlow> Flows { get; init; }

    public IEnumerable<BpmnFlow> Outgoing(string nodeId) => Flows.Where(f => f.SourceRef == nodeId);

    /// <summary>
    /// Từ 1 nút, đi theo luồng tới nút DỪNG kế tiếp (userTask hoặc end). Gateway được giải quyết bằng
    /// <paramref name="decide"/>: trả về giá trị quyết định để chọn nhánh (theo condition của flow).
    /// </summary>
    public BpmnNode? NextStop(string fromNodeId, Func<string, string?>? decide = null)
    {
        var currentId = fromNodeId;
        while (true)
        {
            var flow = ChooseFlow(currentId, decide);
            if (flow is null) return null;
            if (!Nodes.TryGetValue(flow.TargetRef, out var node)) return null;
            if (node.Kind is NodeKind.UserTask or NodeKind.End) return node;
            currentId = node.Id; // Start/Gateway → đi tiếp
        }
    }

    private BpmnFlow? ChooseFlow(string nodeId, Func<string, string?>? decide)
    {
        var outgoing = Outgoing(nodeId).ToList();
        if (outgoing.Count == 0) return null;
        if (outgoing.Count == 1) return outgoing[0];

        // Nhiều luồng ra (exclusiveGateway): chọn theo điều kiện khớp giá trị quyết định.
        var node = Nodes.TryGetValue(nodeId, out var n) ? n : null;
        var decisionValue = node is not null && decide is not null && outgoing[0].ConditionName is { } cond
            ? decide(cond)
            : null;

        var matched = outgoing.FirstOrDefault(f =>
            f.ConditionValue is not null &&
            string.Equals(f.ConditionValue, decisionValue, StringComparison.OrdinalIgnoreCase));

        // fallback: luồng không điều kiện (default), nếu không có → luồng đầu.
        return matched ?? outgoing.FirstOrDefault(f => f.ConditionValue is null) ?? outgoing[0];
    }
}
