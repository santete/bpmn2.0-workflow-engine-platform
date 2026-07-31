using System.Net;
using System.Net.Http.Json;
using Xunit;

namespace WorkflowPlatform.Tests;

public class AuthE2ETests : IClassFixture<InMemoryApiFactory>
{
    private readonly InMemoryApiFactory _factory;
    public AuthE2ETests(InMemoryApiFactory factory) => _factory = factory;

    private sealed record CreatedResponse(Guid Id);

    private HttpClient ClientWithUser(string? user = null, string? role = null)
    {
        var client = _factory.CreateClient();
        if (user is not null) client.DefaultRequestHeaders.Add("X-User", user);
        if (role is not null) client.DefaultRequestHeaders.Add("X-Role", role);
        return client;
    }

    [Fact]
    public async Task Assignee_can_complete_own_task()
    {
        var client = ClientWithUser("thamdinh");
        var create = await client.PostAsJsonAsync("/cases", new { title = "A1" });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        var resp = await client.PostAsJsonAsync($"/cases/{id}/complete-task", new { taskId = "review" });
        Assert.Equal(HttpStatusCode.OK, resp.StatusCode);
    }

    [Fact]
    public async Task Non_assignee_cannot_complete_task()
    {
        var client = ClientWithUser("intruder");
        var create = await client.PostAsJsonAsync("/cases", new { title = "A2" });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        var resp = await client.PostAsJsonAsync($"/cases/{id}/complete-task", new { taskId = "review" });
        Assert.Equal(HttpStatusCode.Forbidden, resp.StatusCode);
    }

    [Fact]
    public async Task Task_without_assignee_is_open_to_anyone()
    {
        // Create a definition without assignees, then create a case with it.
        var client = _factory.CreateClient();
        var defResp = await client.PostAsJsonAsync("/definitions", new
        {
            name = "Open flow",
            steps = new[] { "Step1", "Step2" },
            endsWithDecision = false
        });
        Assert.Equal(HttpStatusCode.Created, defResp.StatusCode);
        var def = await defResp.Content.ReadFromJsonAsync<DefKeyDto>();
        var key = def!.Key;

        var create = await client.PostAsJsonAsync("/cases", new { title = "A3", definitionKey = key });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        var userClient = ClientWithUser("anyone");
        var resp = await userClient.PostAsJsonAsync($"/cases/{id}/complete-task", new { taskId = "s1" });
        Assert.Equal(HttpStatusCode.OK, resp.StatusCode);
    }

    [Fact]
    public async Task Missing_X_User_header_falls_back_to_body_actor()
    {
        var client = _factory.CreateClient();
        var create = await client.PostAsJsonAsync("/cases", new { title = "A4" });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        var resp = await client.PostAsJsonAsync($"/cases/{id}/complete-task",
            new { taskId = "review", actor = "thamdinh" });
        Assert.Equal(HttpStatusCode.OK, resp.StatusCode);
    }

    [Fact]
    public async Task Regular_user_only_sees_own_cases()
    {
        var userA = ClientWithUser("userA");
        var userB = ClientWithUser("userB");

        await userA.PostAsJsonAsync("/cases", new { title = "A-case-1" });
        await userA.PostAsJsonAsync("/cases", new { title = "A-case-2" });
        await userB.PostAsJsonAsync("/cases", new { title = "B-case-1" });

        var aCases = await userA.GetFromJsonAsync<List<CaseViewDto>>("/cases");
        Assert.All(aCases!, c => Assert.Equal("userA", c.Owner));
        Assert.True(aCases!.Count >= 2);

        var bCases = await userB.GetFromJsonAsync<List<CaseViewDto>>("/cases");
        Assert.All(bCases!, c => Assert.Equal("userB", c.Owner));
    }

    [Fact]
    public async Task Admin_sees_all_cases()
    {
        var userA = ClientWithUser("userA");
        await userA.PostAsJsonAsync("/cases", new { title = "A" });
        await userA.PostAsJsonAsync("/cases", new { title = "A2" });

        var admin = ClientWithUser("boss", "admin");
        var cases = await admin.GetFromJsonAsync<List<CaseViewDto>>("/cases");
        Assert.True(cases!.Count >= 2);
    }

    [Fact]
    public async Task User_cannot_see_other_case_by_id()
    {
        var userA = ClientWithUser("userA");
        var create = await userA.PostAsJsonAsync("/cases", new { title = "Secret" });
        var id = (await create.Content.ReadFromJsonAsync<CreatedResponse>())!.Id;

        var userB = ClientWithUser("userB");
        var resp = await userB.GetAsync($"/cases/{id}");
        Assert.Equal(HttpStatusCode.NotFound, resp.StatusCode);
    }

    private sealed record CaseViewDto(Guid Id, string? Owner);
    private sealed record DefKeyDto(string Key);
}
