using System.Text;

namespace WorkflowPlatform.Workflow.Bpmn;

/// <summary>
/// Sinh BPMN 2.0 XML từ mô tả thân thiện (danh sách bước + có/không bước quyết định cuối).
/// Cho phép người dùng ĐỊNH NGHĨA quy trình lúc chạy mà không cần viết XML — thể hiện tính linh động
/// của nền tảng. Engine (bất kỳ adapter nào) chạy được ngay vì chúng vốn generic theo BPMN 2.0.
/// </summary>
public static class BpmnBuilder
{
    private const string Ns = "http://www.omg.org/spec/BPMN/20100524/MODEL";

    public static string Build(string key, string name, IReadOnlyList<(string Id, string Name, string? Assignee)> steps, bool endsWithDecision)
    {
        if (steps.Count == 0)
            throw new ArgumentException("Quy trình phải có ít nhất một bước.", nameof(steps));

        var nodes = new StringBuilder();
        var flows = new StringBuilder();

        nodes.AppendLine($"    <startEvent id=\"start\" name=\"Bat dau\" />");

        var prev = "start";
        foreach (var (id, stepName, assignee) in steps)
        {
            var assigneeAttr = string.IsNullOrWhiteSpace(assignee) ? "" : $" assignee=\"{Esc(assignee)}\"";
            nodes.AppendLine($"    <userTask id=\"{Esc(id)}\" name=\"{Esc(stepName)}\"{assigneeAttr} />");
            flows.AppendLine($"    <sequenceFlow id=\"flow_{Esc(prev)}_{Esc(id)}\" sourceRef=\"{Esc(prev)}\" targetRef=\"{Esc(id)}\" />");
            prev = id;
        }

        if (endsWithDecision)
        {
            nodes.AppendLine($"    <exclusiveGateway id=\"gw\" name=\"Quyet dinh\" />");
            nodes.AppendLine($"    <endEvent id=\"end\" name=\"Hoan tat\" />");
            nodes.AppendLine($"    <endEvent id=\"endRejected\" name=\"Tu choi\" />");
            flows.AppendLine($"    <sequenceFlow id=\"flow_{Esc(prev)}_gw\" sourceRef=\"{Esc(prev)}\" targetRef=\"gw\" />");
            flows.AppendLine($"    <sequenceFlow id=\"flow_gw_end\" sourceRef=\"gw\" targetRef=\"end\"><conditionExpression name=\"decision\">APPROVED</conditionExpression></sequenceFlow>");
            flows.AppendLine($"    <sequenceFlow id=\"flow_gw_rej\" sourceRef=\"gw\" targetRef=\"endRejected\"><conditionExpression name=\"decision\">REJECTED</conditionExpression></sequenceFlow>");
        }
        else
        {
            nodes.AppendLine($"    <endEvent id=\"end\" name=\"Hoan tat\" />");
            flows.AppendLine($"    <sequenceFlow id=\"flow_{Esc(prev)}_end\" sourceRef=\"{Esc(prev)}\" targetRef=\"end\" />");
        }

        return $"""
            <?xml version="1.0" encoding="UTF-8"?>
            <definitions xmlns="{Ns}" targetNamespace="urn:wf" id="defs_{Esc(key)}">
              <process id="{Esc(key)}" name="{Esc(name)}" isExecutable="true">
            {nodes}{flows}  </process>
            </definitions>
            """;
    }

    private static string Esc(string s) => s
        .Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;")
        .Replace("\"", "&quot;").Replace("'", "&apos;");
}
