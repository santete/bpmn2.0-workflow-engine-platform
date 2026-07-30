using WorkflowPlatform.Domain.Cases;
using Xunit;

namespace WorkflowPlatform.Tests;

/// <summary>
/// Mini FIT-007: đảm bảo Domain (PH-4) KHÔNG phụ thuộc workflow/engine — điều kiện tháo lắp (C3).
/// Vi phạm = build đưa được engine SDK vào domain → gãy isolation. Test này chặn cơ học.
/// </summary>
public class ArchitectureIsolationTests
{
    [Fact]
    public void Domain_assembly_does_not_reference_workflow_or_engine()
    {
        var referenced = typeof(Case).Assembly
            .GetReferencedAssemblies()
            .Select(a => a.Name)
            .ToList();

        Assert.DoesNotContain("WorkflowPlatform.Workflow.Abstraction", referenced);
        Assert.DoesNotContain("WorkflowPlatform.Workflow.Adapter.Simple", referenced);
    }
}
