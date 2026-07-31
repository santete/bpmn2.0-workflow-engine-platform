using System.Net.Http.Json;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;

namespace WorkflowPlatform.Tests;

/// <summary>
/// Persistence thật (EF Core + SQLite): dữ liệu nghiệp vụ VÀ vị trí tiến trình sống sót qua "restart"
/// (mô phỏng bằng cách tạo lại host trên cùng file DB).
/// </summary>
public class PersistenceIntegrationTests
{
    private sealed record CreatedResponse(Guid Id);
    private sealed record CaseViewDto(
        Guid Id, string Title, string BusinessStatus, string WorkflowStatus,
        string? CurrentTaskId, string? CurrentTaskName, string? CurrentTaskAssignee);

    private static WebApplicationFactory<Program> SqliteFactory(string dbPath)
        => new WebApplicationFactory<Program>().WithWebHostBuilder(b =>
        {
            b.UseSetting("PERSISTENCE", "sqlite");
            b.UseSetting("DB_PATH", dbPath);
        });

    [Fact]
    public async Task Case_and_workflow_position_survive_restart()
    {
        var dbPath = Path.Combine(Path.GetTempPath(), $"wf-test-{Guid.NewGuid():N}.db");
        Guid id;

        // Phiên 1: tạo hồ sơ + hoàn thành bước "review".
        using (var factory = SqliteFactory(dbPath))
        {
            var client = factory.CreateClient();
            client.DefaultRequestHeaders.Add("X-User", "thamdinh");
            var create = await client.PostAsJsonAsync("/cases", new { title = "Persist", content = "x" });
            id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;
            await client.PostAsJsonAsync($"/cases/{id}/complete-task", new { taskId = "review" });
        }

        // Phiên 2 ("restart"): host mới, cùng file DB → trạng thái phải còn nguyên.
        using (var factory = SqliteFactory(dbPath))
        {
            var client = factory.CreateClient();
            var view = await client.GetFromJsonAsync<CaseViewDto>($"/cases/{id}");
            Assert.NotNull(view);
            Assert.Equal("Persist", view!.Title);
            Assert.Equal("approve", view.CurrentTaskId);      // vị trí tiến trình sống sót
            Assert.Equal("Phe duyet", view.WorkflowStatus);
        }

        try { File.Delete(dbPath); } catch { /* best-effort cleanup */ }
    }
}
