using System.Text.Json.Serialization;
using Microsoft.EntityFrameworkCore;
using Serilog;
using WorkflowPlatform.Api.Infrastructure;
using WorkflowPlatform.Application.Definitions;
using WorkflowPlatform.Application.ReadModel;
using WorkflowPlatform.Domain.Cases;
using WorkflowPlatform.Infrastructure.Persistence;
using WorkflowPlatform.Workflow.Abstraction;
using WorkflowPlatform.Workflow.Abstraction.Contracts;
using WorkflowPlatform.Workflow.Adapter.Replay;
using WorkflowPlatform.Workflow.Adapter.Simple;
using WorkflowPlatform.Workflow.Bpmn;

var builder = WebApplication.CreateBuilder(args);
builder.Host.UseSerilog((ctx, cfg) => cfg.ReadFrom.Configuration(ctx.Configuration));
builder.Services.ConfigureHttpJsonOptions(o => o.SerializerOptions.Converters.Add(new JsonStringEnumConverter()));
var cfg = builder.Configuration;

var persistence = (cfg["PERSISTENCE"] ?? "sqlite").ToLowerInvariant();
var engineChoice = (cfg["WF_ENGINE"] ?? "simple").ToLowerInvariant();

builder.Services.AddSingleton<CaseProjector>();
builder.Services.AddSingleton<IWorkflowEventHandler>(sp => sp.GetRequiredService<CaseProjector>());
builder.Services.AddSingleton<IWorkflowEventPublisher, InProcessEventBus>();
builder.Services.AddSingleton<IProcessPort>(sp =>
    new ResilientProcessPort(
        new WorkflowService(
            sp.GetRequiredService<IEngineAdapter>(),
            sp.GetRequiredService<IWorkflowEventPublisher>()),
        sp.GetRequiredService<ILogger<ResilientProcessPort>>()));
builder.Services.AddExceptionHandler<GlobalExceptionHandler>();
builder.Services.AddProblemDetails();
builder.Services.AddSingleton<CancelBackgroundService>();
builder.Services.AddHostedService(sp => sp.GetRequiredService<CancelBackgroundService>());
builder.Services.AddResponseCompression(o => o.EnableForHttps = true);
builder.Services.AddCors(o => o.AddDefaultPolicy(p =>
    p.WithOrigins("http://localhost:5000", "http://localhost:3000", "http://127.0.0.1:5000")
     .AllowAnyMethod().AllowAnyHeader()));

if (persistence == "sqlite")
{
    var dbPath = cfg["DB_PATH"] ?? "workflow.db";
    builder.Services.AddDbContextFactory<AppDbContext>(o => o.UseSqlite($"Data Source={dbPath}"));
    builder.Services.AddSingleton<ICaseRepository, EfCaseRepository>();
    builder.Services.AddSingleton<ICaseReadStore, EfCaseReadStore>();
    builder.Services.AddSingleton<IReplayLogStore, EfReplayLogStore>();
    builder.Services.AddSingleton<IProcessDefinitionStore, EfProcessDefinitionStore>();
    builder.Services.AddSingleton<ICaseHistoryStore, EfCaseHistoryStore>();
    builder.Services.AddSingleton<IEngineAdapter, ReplayEngineAdapter>();
}
else
{
    builder.Services.AddSingleton<ICaseRepository, InMemoryCaseRepository>();
    builder.Services.AddSingleton<ICaseReadStore, InMemoryCaseReadStore>();
    builder.Services.AddSingleton<IReplayLogStore, InMemoryReplayLogStore>();
    builder.Services.AddSingleton<IProcessDefinitionStore, InMemoryProcessDefinitionStore>();
    builder.Services.AddSingleton<ICaseHistoryStore, InMemoryCaseHistoryStore>();
    if (engineChoice == "replay")
        builder.Services.AddSingleton<IEngineAdapter, ReplayEngineAdapter>();
    else
        builder.Services.AddSingleton<IEngineAdapter, SimpleBpmnEngineAdapter>();
}

var app = builder.Build();

app.UseResponseCompression();
app.UseCors();
app.UseMiddleware<SecurityHeadersMiddleware>();
app.UseDefaultFiles();
app.UseStaticFiles();
app.UseMiddleware<RateLimitMiddleware>();
app.UseMiddleware<TraceIdMiddleware>();
app.UseMiddleware<IdentityMiddleware>();
app.UseExceptionHandler();

if (persistence == "sqlite")
{
    using var ctx = app.Services.GetRequiredService<IDbContextFactory<AppDbContext>>().CreateDbContext();
    ctx.Database.EnsureCreated();
}

// Seed quy trình mặc định (nếu chưa có), rồi deploy TẤT CẢ định nghĩa đã lưu.
var defStore = app.Services.GetRequiredService<IProcessDefinitionStore>();
if (!defStore.All().Any())
{
    defStore.Save(new ProcessDefinitionSpec
    {
        Key = "case-approval",
        Name = "Quy trinh phe duyet ho so",
        EndsWithDecision = true,
        Steps = new()
        {
            new StepSpec { Id = "review", Name = "Tham dinh ho so", Assignee = "thamdinh" },
            new StepSpec { Id = "approve", Name = "Phe duyet", Assignee = "lanhdao" }
        }
    });
}
var processPort = app.Services.GetRequiredService<IProcessPort>();
foreach (var spec in defStore.All())
    await processPort.DeployDefinitionAsync(new CanonicalBpmn(spec.Key, ToXml(spec)));

// --- Định nghĩa quy trình (tạo/sửa lúc chạy — tính linh động) ---
app.MapGet("/definitions", (IProcessDefinitionStore store) => Results.Ok(store.All()));

app.MapPost("/definitions", async (CreateDefinitionRequest req, IProcessDefinitionStore store, IProcessPort wf) =>
{
    if (req.Steps is null || req.Steps.Length == 0)
        return Results.BadRequest(new { error = "Quy trình cần ít nhất một bước." });

    var key = $"wf-{Guid.NewGuid():N}"[..11];
    var assignees = req.Assignees ?? Array.Empty<string?>();
    var spec = new ProcessDefinitionSpec
    {
        Key = key,
        Name = string.IsNullOrWhiteSpace(req.Name) ? key : req.Name.Trim(),
        EndsWithDecision = req.EndsWithDecision,
        Steps = req.Steps
            .Where(n => !string.IsNullOrWhiteSpace(n))
            .Select((n, i) => new StepSpec
            {
                Id = $"s{i + 1}",
                Name = n.Trim(),
                Assignee = i < assignees.Length && !string.IsNullOrWhiteSpace(assignees[i]) ? assignees[i]!.Trim() : null
            })
            .ToList()
    };
    if (spec.Steps.Count == 0)
        return Results.BadRequest(new { error = "Quy trình cần ít nhất một bước hợp lệ." });

    store.Save(spec);
    await wf.DeployDefinitionAsync(new CanonicalBpmn(spec.Key, ToXml(spec)));
    return Results.Created($"/definitions/{key}", spec);
});

// --- Hồ sơ (instance của một quy trình bất kỳ) ---
app.MapPost("/cases", async (CreateCaseRequest req, ICaseRepository repo, CaseProjector projector, IProcessPort wf, HttpContext ctx) =>
{
    var definitionKey = string.IsNullOrWhiteSpace(req.DefinitionKey) ? "case-approval" : req.DefinitionKey!;
    var owner = ctx.Items["User"] as string ?? req.CreatedBy;
    var @case = Case.Create(req.Title, req.Content ?? string.Empty);
    repo.Add(@case);
    projector.OnCaseCreated(@case.Id, @case.Title, definitionKey, owner);

    await wf.StartProcessAsync(new StartProcessCommand(
        ProcessDefinitionKey: definitionKey,
        BusinessKey: @case.Id.ToString(),
        Variables: new Dictionary<string, ProcessVariable> { ["caseRef"] = ProcessVariable.Ref("case", @case.Id.ToString()) },
        Initiator: owner ?? "system"));

    return Results.Created($"/cases/{@case.Id}", new { id = @case.Id });
});

app.MapGet("/cases", (ICaseReadStore store, HttpContext ctx) =>
{
    var currentUser = ctx.Items["User"] as string;
    var isAdmin = "admin".Equals(ctx.Items["Role"] as string, StringComparison.OrdinalIgnoreCase);
    var all = store.All();
    if (isAdmin || currentUser is null) return Results.Ok(all);
    return Results.Ok(all.Where(v => v.Owner == currentUser).ToList());
});

static bool IsOwnerOrAdmin(CaseView view, HttpContext ctx)
{
    var currentUser = ctx.Items["User"] as string;
    if (currentUser is null) return true;
    if ("admin".Equals(ctx.Items["Role"] as string, StringComparison.OrdinalIgnoreCase)) return true;
    return view.Owner == currentUser;
}

app.MapGet("/cases/{id:guid}", (Guid id, ICaseReadStore store, HttpContext ctx) =>
{
    if (store.Get(id) is not { } view) return Results.NotFound();
    if (!IsOwnerOrAdmin(view, ctx)) return Results.NotFound();
    ctx.Response.Headers["ETag"] = $"\"{view.Version}\"";
    return Results.Ok(view);
});

app.MapPost("/cases/{id:guid}/complete-task", async (Guid id, CompleteTaskRequest req, IProcessPort wf, ICaseReadStore store, IProcessDefinitionStore defStore, HttpContext ctx) =>
{
    var view = store.Get(id);
    if (view is null) return Results.NotFound();

    var ifMatch = ctx.Request.Headers.IfMatch;
    if (ifMatch.Count > 0)
    {
        var expected = ifMatch.ToString().Trim('"');
        if (view.Version.ToString() != expected)
            return Results.StatusCode(StatusCodes.Status412PreconditionFailed);
    }

    var actor = ctx.Items["User"] as string ?? req.Actor ?? "system";

    // Counter-sign logic: nếu đang pending → chỉ countersigner mới được complete
    if (view.PendingCounterSign)
    {
        if (!string.Equals(view.CounterSigner, actor, StringComparison.OrdinalIgnoreCase))
            return Results.Json(new { error = $"Cần người phê duyệt '{view.CounterSigner}' để hoàn tất, không phải '{actor}'." },
                statusCode: StatusCodes.Status403Forbidden);

        // Countersigner approved → real complete
        await wf.CompleteUserTaskAsync(new CompleteTaskCommand(
            BusinessKey: id.ToString(),
            TaskId: req.TaskId,
            Variables: new Dictionary<string, ProcessVariable> { ["decision"] = ProcessVariable.Enum(req.Decision ?? "APPROVED") },
            Actor: actor));
        var updView = store.Get(id);
        return updView is not null ? Results.Ok(updView) : Results.NotFound();
    }

    // Assignee check
    if (!string.IsNullOrWhiteSpace(view.CurrentTaskAssignee)
        && !string.Equals(view.CurrentTaskAssignee, actor, StringComparison.OrdinalIgnoreCase))
    {
        return Results.Json(new { error = $"Bước này được phân công cho '{view.CurrentTaskAssignee}', không phải '{actor}'." },
            statusCode: StatusCodes.Status403Forbidden);
    }

    // Check if current step requires counter-sign
    var def = defStore.Get(view.DefinitionKey);
    var currentStep = def?.Steps.FirstOrDefault(s => s.Id == view.CurrentTaskId);
    if (currentStep is { RequiresCounterSign: true })
    {
        view.CounterSigner = currentStep.CounterSigner;
        view.PendingCounterSign = true;
        view.WorkflowStatus = $"Cho ky duyet ({currentStep.CounterSigner})";
        view.Version = Guid.NewGuid();
        store.Upsert(view);
        return Results.Ok(view);
    }

    await wf.CompleteUserTaskAsync(new CompleteTaskCommand(
        BusinessKey: id.ToString(),
        TaskId: req.TaskId,
        Variables: new Dictionary<string, ProcessVariable> { ["decision"] = ProcessVariable.Enum(req.Decision ?? "APPROVED") },
        Actor: actor));

    var endView = store.Get(id);
    return endView is not null ? Results.Ok(endView) : Results.NotFound();
});

app.MapPost("/cases/{id:guid}/cancel", async (Guid id, ICaseReadStore store, CancelBackgroundService bg) =>
{
    var view = store.Get(id);
    if (view is null) return Results.NotFound();
    if (view.CurrentTaskId is null) return Results.Conflict();

    await bg.EnqueueAsync(new CancelCommand(id.ToString()));
    return Results.Accepted();
});

app.MapGet("/cases/{id:guid}/history", (Guid id, ICaseHistoryStore historyStore, ICaseReadStore store)
    => store.Get(id) is null ? Results.NotFound() : Results.Ok(historyStore.List(id)));

app.MapGet("/cases/{id:guid}/history/verify", (Guid id, ICaseHistoryStore historyStore, ICaseReadStore store)
    => store.Get(id) is null ? Results.NotFound()
        : historyStore.VerifyIntegrity(id) ? Results.Ok(new { integrity = "valid" }) : Results.Conflict(new { integrity = "tampered", message = "Audit trail checksum chain is broken." }));

app.MapGet("/processes/{key}/state", async (string key, IProcessPort wf) =>
{
    var state = await wf.GetProcessStateAsync(key);
    return state.Status == WorkflowPlatform.Workflow.Abstraction.Contracts.ProcessStatus.NotFound
        ? Results.NotFound()
        : Results.Ok(state);
});

app.MapGet("/health/live", () => Results.Ok(new { status = "healthy" }));

app.MapGet("/health/ready", async (IHostApplicationLifetime lifetime, IServiceProvider sp) =>
{
    try
    {
        if (sp.GetService<IDbContextFactory<AppDbContext>>() is { } factory)
        {
            using var ctx = await factory.CreateDbContextAsync();
            await ctx.Database.CanConnectAsync();
        }
        return Results.Ok(new { status = "healthy" });
    }
    catch
    {
        return Results.Json(new { status = "unhealthy", detail = "Database connection failed." }, statusCode: 503);
    }
});

app.Run();

static string ToXml(ProcessDefinitionSpec spec)
    => BpmnBuilder.Build(spec.Key, spec.Name,
        spec.Steps.Select(s => (s.Id, s.Name, s.Assignee)).ToList(), spec.EndsWithDecision);

public sealed record CreateDefinitionRequest(string Name, string[] Steps, bool EndsWithDecision, string?[]? Assignees);
public sealed record CreateCaseRequest(string Title, string? Content, string? DefinitionKey, string? CreatedBy);
public sealed record CompleteTaskRequest(string TaskId, string? Decision, string? Actor);

public partial class Program { }
