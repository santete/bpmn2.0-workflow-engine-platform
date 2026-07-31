namespace WorkflowPlatform.Api.Infrastructure;

public sealed class IdentityMiddleware
{
    private readonly RequestDelegate _next;

    public IdentityMiddleware(RequestDelegate next) => _next = next;

    public async Task InvokeAsync(HttpContext ctx)
    {
        var user = ctx.Request.Headers["X-User"].FirstOrDefault();
        var role = ctx.Request.Headers["X-Role"].FirstOrDefault();

        if (!string.IsNullOrWhiteSpace(user)) ctx.Items["User"] = user.Trim();
        if (!string.IsNullOrWhiteSpace(role)) ctx.Items["Role"] = role.Trim();

        await _next(ctx);
    }
}
