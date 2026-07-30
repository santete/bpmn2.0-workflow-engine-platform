using System.Net;
using System.Net.Http.Json;
using Xunit;

namespace WorkflowPlatform.Tests;

/// <summary>
/// Tính linh động: định nghĩa một quy trình MỚI lúc chạy (qua API), rồi mở hồ sơ chạy theo nó —
/// không sửa/biên dịch lại code. Chứng minh nền tảng workflow cấu hình được.
/// </summary>
public class DefinitionManagementTests : IClassFixture<InMemoryApiFactory>
{
    private readonly InMemoryApiFactory _factory;
    public DefinitionManagementTests(InMemoryApiFactory factory) => _factory = factory;

    private sealed record CreatedResponse(Guid Id);
    private sealed record StepDto(string Id, string Name);
    private sealed record DefDto(string Key, string Name, StepDto[] Steps, bool EndsWithDecision);
    private sealed record CaseViewDto(Guid Id, string Title, string DefinitionKey,
        string BusinessStatus, string WorkflowStatus, string? CurrentTaskId, string? CurrentTaskName);

    [Fact]
    public async Task Define_custom_workflow_then_run_an_instance_through_it()
    {
        var client = _factory.CreateClient();

        // 1) Định nghĩa quy trình 3 bước + quyết định cuối.
        var defResp = await client.PostAsJsonAsync("/definitions", new
        {
            name = "Quy trinh cap phep",
            steps = new[] { "Kiem tra", "Xac minh", "Quyet dinh" },
            endsWithDecision = true
        });
        Assert.Equal(HttpStatusCode.Created, defResp.StatusCode);
        var spec = await defResp.Content.ReadFromJsonAsync<DefDto>();
        Assert.Equal(3, spec!.Steps.Length);
        var key = spec.Key;

        // 2) Mở hồ sơ chạy theo quy trình vừa định nghĩa.
        var create = await client.PostAsJsonAsync("/cases", new { title = "HS cap phep", definitionKey = key });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        var v0 = await client.GetFromJsonAsync<CaseViewDto>($"/cases/{id}");
        Assert.Equal(key, v0!.DefinitionKey);
        Assert.Equal("s1", v0.CurrentTaskId);
        Assert.Equal("Kiem tra", v0.CurrentTaskName);

        // 3) Đi qua các bước động.
        var v1 = await (await client.PostAsJsonAsync($"/cases/{id}/complete-task", new { taskId = "s1" }))
            .Content.ReadFromJsonAsync<CaseViewDto>();
        Assert.Equal("s2", v1!.CurrentTaskId);
        Assert.Equal("Xac minh", v1.CurrentTaskName);

        var v2 = await (await client.PostAsJsonAsync($"/cases/{id}/complete-task", new { taskId = "s2" }))
            .Content.ReadFromJsonAsync<CaseViewDto>();
        Assert.Equal("s3", v2!.CurrentTaskId);

        // 4) Bước quyết định → từ chối.
        var v3 = await (await client.PostAsJsonAsync($"/cases/{id}/complete-task",
                new { taskId = "s3", decision = "REJECTED" }))
            .Content.ReadFromJsonAsync<CaseViewDto>();
        Assert.Equal("Tu choi", v3!.WorkflowStatus);
        Assert.Equal("Rejected", v3.BusinessStatus);
        Assert.Null(v3.CurrentTaskId);
    }
}
