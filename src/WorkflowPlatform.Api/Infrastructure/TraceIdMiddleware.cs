namespace WorkflowPlatform.Api.Infrastructure;

public sealed class TraceIdMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<TraceIdMiddleware> _logger;

    public TraceIdMiddleware(RequestDelegate next, ILogger<TraceIdMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext ctx)
    {
        var traceId = ctx.TraceIdentifier;
        ctx.Response.Headers["X-Trace-Id"] = traceId;

        _logger.LogInformation("Request {Method} {Path} {TraceId} started",
            ctx.Request.Method, ctx.Request.Path, traceId);

        await _next(ctx);

        _logger.LogInformation("Response {StatusCode} {Method} {Path} {TraceId}",
            ctx.Response.StatusCode, ctx.Request.Method, ctx.Request.Path, traceId);
    }
}
