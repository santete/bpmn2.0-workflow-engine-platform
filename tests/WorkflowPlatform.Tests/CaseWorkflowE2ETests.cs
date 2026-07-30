using System.Net;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Hosting;
using Xunit;

namespace WorkflowPlatform.Tests;

/// <summary>
/// E2E xuyên mọi tầng: HTTP → domain → IProcessPort → engine adapter → event → read model → HTTP.
/// Chạy trên cả 2 engine (FIT-010 ở tầng HTTP). Chế độ in-memory để test nhanh & cô lập.
/// </summary>
public class CaseWorkflowE2ETests : IClassFixture<InMemoryApiFactory>
{
    private readonly InMemoryApiFactory _factory;

    public CaseWorkflowE2ETests(InMemoryApiFactory factory) => _factory = factory;

    private sealed record CreatedResponse(Guid Id);
    private sealed record CaseViewDto(
        Guid Id, string Title, string BusinessStatus, string WorkflowStatus,
        string? CurrentTaskId, string? CurrentTaskName);

    [Theory]
    [InlineData("simple")]
    [InlineData("replay")]
    public async Task Full_case_approval_flow_advances_through_workflow(string engine)
    {
        var client = _factory
            .WithWebHostBuilder(b => b.UseSetting("WF_ENGINE", engine))
            .CreateClient();

        var create = await client.PostAsJsonAsync("/cases", new { title = "Ho so A", content = "noi dung mat" });
        Assert.Equal(HttpStatusCode.Created, create.StatusCode);
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        var afterCreate = await client.GetFromJsonAsync<CaseViewDto>($"/cases/{id}");
        Assert.Equal("review", afterCreate!.CurrentTaskId);
        Assert.Equal("Tham dinh ho so", afterCreate.WorkflowStatus);   // status = tên bước động
        Assert.Equal("InReview", afterCreate.BusinessStatus);

        var afterReview = await (await client.PostAsJsonAsync(
            $"/cases/{id}/complete-task", new { taskId = "review" })).Content.ReadFromJsonAsync<CaseViewDto>();
        Assert.Equal("approve", afterReview!.CurrentTaskId);
        Assert.Equal("Phe duyet", afterReview.WorkflowStatus);

        var afterApprove = await (await client.PostAsJsonAsync(
            $"/cases/{id}/complete-task", new { taskId = "approve" })).Content.ReadFromJsonAsync<CaseViewDto>();
        Assert.Null(afterApprove!.CurrentTaskId);
        Assert.Equal("Hoan tat", afterApprove.WorkflowStatus);
        Assert.Equal("Approved", afterApprove.BusinessStatus);
    }

    [Fact]
    public async Task Reject_decision_routes_case_to_rejected_branch()
    {
        var client = _factory.CreateClient();

        var create = await client.PostAsJsonAsync("/cases", new { title = "Ho so B", content = "x" });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        await client.PostAsJsonAsync($"/cases/{id}/complete-task", new { taskId = "review" });
        var afterReject = await (await client.PostAsJsonAsync(
            $"/cases/{id}/complete-task", new { taskId = "approve", decision = "REJECTED" }))
            .Content.ReadFromJsonAsync<CaseViewDto>();

        Assert.Equal("Tu choi", afterReject!.WorkflowStatus);
        Assert.Equal("Rejected", afterReject.BusinessStatus);
        Assert.Null(afterReject.CurrentTaskId);
    }

    [Fact]
    public async Task Unknown_case_returns_404()
    {
        var client = _factory.CreateClient();
        var resp = await client.GetAsync($"/cases/{Guid.NewGuid()}");
        Assert.Equal(HttpStatusCode.NotFound, resp.StatusCode);
    }
}
