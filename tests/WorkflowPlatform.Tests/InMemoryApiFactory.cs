using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;

namespace WorkflowPlatform.Tests;

/// <summary>Factory chạy API ở chế độ in-memory (test nhanh, cô lập, không đụng file SQLite).</summary>
public sealed class InMemoryApiFactory : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
        => builder.UseSetting("PERSISTENCE", "inmemory");
}
