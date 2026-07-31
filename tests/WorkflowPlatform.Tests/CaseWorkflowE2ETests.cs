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

    private HttpClient ClientAsWeb(string? user = null)
    {
        var c = _factory.CreateClient();
        if (user is not null) c.DefaultRequestHeaders.Add("X-User", user);
        return c;
    }

    private sealed record CreatedResponse(Guid Id);
    private sealed record CaseViewDto(
        Guid Id, string Title, string BusinessStatus, string WorkflowStatus,
        string? CurrentTaskId, string? CurrentTaskName, string? CurrentTaskAssignee);
    private sealed record HistoryEntryDto(
        Guid CaseId, string Kind, string? TaskId, string? TaskName,
        string? Actor, string? Decision, DateTimeOffset OccurredAt);

    [Theory]
    [InlineData("simple")]
    [InlineData("replay")]
    public async Task Full_case_approval_flow_advances_through_workflow(string engine)
    {
        var client = _factory
            .WithWebHostBuilder(b => b.UseSetting("WF_ENGINE", engine))
            .CreateClient();
        client.DefaultRequestHeaders.Add("X-User", "thamdinh");

        var create = await client.PostAsJsonAsync("/cases", new { title = "Ho so A", content = "noi dung mat" });
        Assert.Equal(HttpStatusCode.Created, create.StatusCode);
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        var afterCreate = await client.GetFromJsonAsync<CaseViewDto>($"/cases/{id}");
        Assert.Equal("review", afterCreate!.CurrentTaskId);
        Assert.Equal("thamdinh", afterCreate.CurrentTaskAssignee);
        Assert.Equal("Tham dinh ho so", afterCreate.WorkflowStatus);
        Assert.Equal("InReview", afterCreate.BusinessStatus);

        var afterReview = await (await client.PostAsJsonAsync(
            $"/cases/{id}/complete-task", new { taskId = "review" })).Content.ReadFromJsonAsync<CaseViewDto>();
        Assert.Equal("approve", afterReview!.CurrentTaskId);
        Assert.Equal("Phe duyet", afterReview.WorkflowStatus);

        // Switch to approver
        client.DefaultRequestHeaders.Remove("X-User");
        client.DefaultRequestHeaders.Add("X-User", "lanhdao");
        var afterApprove = await (await client.PostAsJsonAsync(
            $"/cases/{id}/complete-task", new { taskId = "approve" })).Content.ReadFromJsonAsync<CaseViewDto>();
        Assert.Null(afterApprove!.CurrentTaskId);
        Assert.Equal("Hoan tat", afterApprove.WorkflowStatus);
        Assert.Equal("Approved", afterApprove.BusinessStatus);
    }

    [Fact]
    public async Task Reject_decision_routes_case_to_rejected_branch()
    {
        var client = ClientAsWeb("thamdinh");

        var create = await client.PostAsJsonAsync("/cases", new { title = "Ho so B", content = "x" });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        await client.PostAsJsonAsync($"/cases/{id}/complete-task", new { taskId = "review" });
        client.DefaultRequestHeaders.Remove("X-User");
        client.DefaultRequestHeaders.Add("X-User", "lanhdao");
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

    [Fact]
    public async Task History_endpoint_returns_entries_in_order()
    {
        var client = ClientAsWeb("thamdinh");

        var create = await client.PostAsJsonAsync("/cases", new { title = "History test" });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        await client.PostAsJsonAsync($"/cases/{id}/complete-task",
            new { taskId = "review", decision = "APPROVED" });
        client.DefaultRequestHeaders.Remove("X-User");
        client.DefaultRequestHeaders.Add("X-User", "lanhdao");
        await client.PostAsJsonAsync($"/cases/{id}/complete-task",
            new { taskId = "approve", decision = "REJECTED" });

        var history = await client.GetFromJsonAsync<List<HistoryEntryDto>>($"/cases/{id}/history");
        Assert.Equal(3, history!.Count);
        Assert.Equal("TaskCompleted", history[0].Kind);
        Assert.Equal("review", history[0].TaskId);
        Assert.Equal("thamdinh", history[0].Actor);
        Assert.Equal("TaskCompleted", history[1].Kind);
        Assert.Equal("approve", history[1].TaskId);
        Assert.Equal("lanhdao", history[1].Actor);
        Assert.Equal("REJECTED", history[1].Decision);
        Assert.Equal("ProcessRejected", history[2].Kind);
    }

    [Fact]
    public async Task History_endpoint_returns_404_for_unknown_case()
    {
        var client = _factory.CreateClient();
        var resp = await client.GetAsync($"/cases/{Guid.NewGuid()}/history");
        Assert.Equal(HttpStatusCode.NotFound, resp.StatusCode);
    }

    [Fact]
    public async Task Process_state_endpoint_returns_state_and_404()
    {
        var client = _factory.CreateClient();

        var create = await client.PostAsJsonAsync("/cases", new { title = "State test" });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        var resp = await client.GetFromJsonAsync<ProcessStateViewJson>($"/processes/{id}/state");
        Assert.Equal("Running", resp!.Status);
        Assert.Single(resp.ActiveTasks);

        var nf = await client.GetAsync($"/processes/{Guid.NewGuid()}/state");
        Assert.Equal(HttpStatusCode.NotFound, nf.StatusCode);
    }

    [Fact]
    public async Task Complete_with_correct_version_succeeds()
    {
        var client = ClientAsWeb("thamdinh");

        var create = await client.PostAsJsonAsync("/cases", new { title = "Concurrency OK" });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        var getResp = await client.GetAsync($"/cases/{id}");
        var etag = getResp.Headers.ETag!.Tag; // "\"guid\""

        var req = new HttpRequestMessage(HttpMethod.Post, $"/cases/{id}/complete-task")
        {
            Content = JsonContent.Create(new { taskId = "review" })
        };
        req.Headers.TryAddWithoutValidation("If-Match", etag);
        var resp = await client.SendAsync(req);
        Assert.Equal(HttpStatusCode.OK, resp.StatusCode);
    }

    [Fact]
    public async Task Complete_with_stale_version_returns_412()
    {
        var client = ClientAsWeb("thamdinh");

        var create = await client.PostAsJsonAsync("/cases", new { title = "Concurrency KO" });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        var v0 = (await client.GetAsync($"/cases/{id}")).Headers.ETag!.Tag;

        // complete once → version bumps
        var ok = new HttpRequestMessage(HttpMethod.Post, $"/cases/{id}/complete-task")
        {
            Content = JsonContent.Create(new { taskId = "review" })
        };
        ok.Headers.TryAddWithoutValidation("If-Match", v0);
        Assert.Equal(HttpStatusCode.OK, (await client.SendAsync(ok)).StatusCode);

        // retry with stale v0 → 412
        var ko = new HttpRequestMessage(HttpMethod.Post, $"/cases/{id}/complete-task")
        {
            Content = JsonContent.Create(new { taskId = "approve" })
        };
        ko.Headers.TryAddWithoutValidation("If-Match", v0);
        Assert.Equal(HttpStatusCode.PreconditionFailed, (await client.SendAsync(ko)).StatusCode);
    }

    [Fact]
    public async Task Complete_without_if_match_still_works()
    {
        var client = ClientAsWeb("thamdinh");

        var create = await client.PostAsJsonAsync("/cases", new { title = "No ETag" });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        var resp = await client.PostAsJsonAsync($"/cases/{id}/complete-task", new { taskId = "review" });
        Assert.Equal(HttpStatusCode.OK, resp.StatusCode);
    }

    [Fact]
    public async Task Cancel_running_case_returns_202_and_marks_cancelled()
    {
        var client = ClientAsWeb("thamdinh");
        var create = await client.PostAsJsonAsync("/cases", new { title = "Cancel me" });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        var resp = await client.PostAsJsonAsync($"/cases/{id}/cancel", new { });
        Assert.Equal(HttpStatusCode.Accepted, resp.StatusCode);

        await Task.Delay(200);
        var view2 = await client.GetFromJsonAsync<CaseViewDto>($"/cases/{id}");
        Assert.Equal("Da huy", view2!.WorkflowStatus);
        Assert.Null(view2!.CurrentTaskId);

        var history = await client.GetFromJsonAsync<List<HistoryEntryDto>>($"/cases/{id}/history");
        Assert.Contains(history!, e => e.Kind == "ProcessCancelled");
    }

    [Fact]
    public async Task Cancel_ended_case_returns_409()
    {
        var client = ClientAsWeb("thamdinh");
        var create = await client.PostAsJsonAsync("/cases", new { title = "Already done" });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;
        await client.PostAsJsonAsync($"/cases/{id}/complete-task", new { taskId = "review" });
        client.DefaultRequestHeaders.Remove("X-User");
        client.DefaultRequestHeaders.Add("X-User", "lanhdao");
        await client.PostAsJsonAsync($"/cases/{id}/complete-task", new { taskId = "approve" });

        var resp = await client.PostAsync($"/cases/{id}/cancel", null);
        Assert.Equal(HttpStatusCode.Conflict, resp.StatusCode);
    }

    [Fact]
    public async Task Cancel_unknown_case_returns_404()
    {
        var client = ClientAsWeb("thamdinh");
        var resp = await client.PostAsync($"/cases/{Guid.NewGuid()}/cancel", null);
        Assert.Equal(HttpStatusCode.NotFound, resp.StatusCode);
    }

    private sealed record ProcessStateViewJson(string BusinessKey, string DefinitionKey, string Status, TaskViewJson[] ActiveTasks);
    private sealed record TaskViewJson(string TaskId, string Name);

    [Fact]
    public async Task Health_live_returns_200()
    {
        var client = _factory.CreateClient();
        var resp = await client.GetAsync("/health/live");
        Assert.Equal(HttpStatusCode.OK, resp.StatusCode);
    }

    [Fact]
    public async Task Health_ready_returns_200()
    {
        var client = _factory.CreateClient();
        var resp = await client.GetAsync("/health/ready");
        Assert.Equal(HttpStatusCode.OK, resp.StatusCode);
    }
}
