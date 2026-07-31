using System.Xml.Linq;

namespace WorkflowPlatform.Workflow.Bpmn;

/// <summary>Parse BPMN 2.0 XML (C1): startEvent/userTask/exclusiveGateway/endEvent + sequenceFlow (có điều kiện).</summary>
public static class BpmnParser
{
    private static readonly XNamespace Bpmn = "http://www.omg.org/spec/BPMN/20100524/MODEL";

    public static BpmnDefinition Parse(string xml)
    {
        var doc = XDocument.Parse(xml);
        var process = doc.Descendants(Bpmn + "process").FirstOrDefault()
            ?? throw new FormatException("BPMN không có phần tử <process>.");

        var key = (string?)process.Attribute("id") ?? throw new FormatException("<process> thiếu id.");
        var name = (string?)process.Attribute("name") ?? key;

        var nodes = new Dictionary<string, BpmnNode>();
        void Add(string element, NodeKind kind)
        {
            foreach (var el in process.Elements(Bpmn + element))
            {
                var id = (string?)el.Attribute("id");
                if (string.IsNullOrEmpty(id)) continue;
                var assignee = kind == NodeKind.UserTask ? (string?)el.Attribute("assignee") : null;
                nodes[id] = new BpmnNode(id, (string?)el.Attribute("name") ?? id, kind, assignee);
            }
        }
        Add("startEvent", NodeKind.Start);
        Add("userTask", NodeKind.UserTask);
        Add("exclusiveGateway", NodeKind.Gateway);
        Add("parallelGateway", NodeKind.ParallelGateway);
        Add("endEvent", NodeKind.End);

        var flows = new List<BpmnFlow>();
        foreach (var f in process.Elements(Bpmn + "sequenceFlow"))
        {
            var id = (string?)f.Attribute("id") ?? Guid.NewGuid().ToString("N");
            var source = (string?)f.Attribute("sourceRef");
            var target = (string?)f.Attribute("targetRef");
            if (string.IsNullOrEmpty(source) || string.IsNullOrEmpty(target)) continue;

            // Điều kiện dạng: <conditionExpression name="decision">APPROVED</conditionExpression>
            var cond = f.Element(Bpmn + "conditionExpression");
            flows.Add(new BpmnFlow(id, source, target,
                (string?)cond?.Attribute("name"),
                cond is null ? null : cond.Value.Trim()));
        }

        var start = nodes.Values.FirstOrDefault(n => n.Kind == NodeKind.Start)
            ?? throw new FormatException("BPMN không có startEvent.");

        return new BpmnDefinition
        {
            Key = key, Name = name, StartNodeId = start.Id,
            Nodes = nodes, Flows = flows
        };
    }
}
