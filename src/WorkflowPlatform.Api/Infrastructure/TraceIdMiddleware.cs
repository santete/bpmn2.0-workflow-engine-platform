namespace WorkflowPlatform.Api.Infrastructure;

public sealed class TraceIdMiddleware
{
    private readonly RequestDelegate _next;

    public TraceIdMiddleware(RequestDelegate next) => _next = next;

    public async Task InvokeAsync(HttpContext ctx)
    {
        ctx.Response.Headers["X-Trace-Id"] = ctx.TraceIdentifier;
        await _next(ctx);
    }
}
