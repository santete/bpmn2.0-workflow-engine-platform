namespace WorkflowPlatform.Tests;

internal static class TestBpmn
{
    // start → review → approve → gateway → (APPROVED → end) | (REJECTED → endRejected)
    public const string CaseApproval = """
        <?xml version="1.0" encoding="UTF-8"?>
        <definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="defs" targetNamespace="urn:test">
          <process id="case-approval" name="Case Approval" isExecutable="true">
            <startEvent id="start" name="Start" />
            <sequenceFlow id="f1" sourceRef="start" targetRef="review" />
            <userTask id="review" name="Tham dinh" assignee="thamdinh" />
            <sequenceFlow id="f2" sourceRef="review" targetRef="approve" />
            <userTask id="approve" name="Phe duyet" assignee="lanhdao" />
            <sequenceFlow id="f3" sourceRef="approve" targetRef="gw" />
            <exclusiveGateway id="gw" name="Quyet dinh" />
            <sequenceFlow id="f4" sourceRef="gw" targetRef="end">
              <conditionExpression name="decision">APPROVED</conditionExpression>
            </sequenceFlow>
            <sequenceFlow id="f5" sourceRef="gw" targetRef="endRejected">
              <conditionExpression name="decision">REJECTED</conditionExpression>
            </sequenceFlow>
            <endEvent id="end" name="End" />
            <endEvent id="endRejected" name="Rejected" />
          </process>
        </definitions>
        """;

    // start → fork → (parallelA | parallelB) → join → end
    public const string ParallelFork = """
        <?xml version="1.0" encoding="UTF-8"?>
        <definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="defs2" targetNamespace="urn:test">
          <process id="parallel" name="Parallel Flow" isExecutable="true">
            <startEvent id="start" name="Start" />
            <sequenceFlow id="f0" sourceRef="start" targetRef="fork" />
            <parallelGateway id="fork" name="Fork" />
            <sequenceFlow id="f1" sourceRef="fork" targetRef="taskA" />
            <userTask id="taskA" name="Nhanh A" />
            <sequenceFlow id="f2" sourceRef="taskA" targetRef="join" />
            <sequenceFlow id="f3" sourceRef="fork" targetRef="taskB" />
            <userTask id="taskB" name="Nhanh B" />
            <sequenceFlow id="f4" sourceRef="taskB" targetRef="join" />
            <parallelGateway id="join" name="Join" />
            <sequenceFlow id="f5" sourceRef="join" targetRef="end" />
            <endEvent id="end" name="End" />
          </process>
        </definitions>
        """;
}
