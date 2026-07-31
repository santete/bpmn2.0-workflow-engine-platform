using System.Collections.Concurrent;

namespace WorkflowPlatform.Api.Infrastructure;

public sealed class RateLimitMiddleware
{
    private readonly RequestDelegate _next;
    private static readonly ConcurrentDictionary<string, (int Count, DateTime Reset)> _clients = new();
    private const int MaxRequests = 100;
    private const int WindowSeconds = 60;

    public RateLimitMiddleware(RequestDelegate next) => _next = next;

    public async Task InvokeAsync(HttpContext ctx)
    {
        if (ctx.Request.Path.StartsWithSegments("/health"))
        {
            await _next(ctx);
            return;
        }

        var key = ctx.Items["User"] as string ?? ctx.Connection.RemoteIpAddress?.ToString() ?? "anon";
        var now = DateTime.UtcNow;

        var entry = _clients.GetOrAdd(key, _ => (0, now.AddSeconds(WindowSeconds)));

        if (now > entry.Reset)
        {
            _clients.TryUpdate(key, (1, now.AddSeconds(WindowSeconds)), entry);
        }
        else
        {
            var newCount = entry.Count + 1;
            if (newCount > MaxRequests)
            {
                ctx.Response.StatusCode = StatusCodes.Status429TooManyRequests;
                ctx.Response.Headers["Retry-After"] = ((int)(entry.Reset - now).TotalSeconds).ToString();
                await ctx.Response.WriteAsync("Rate limit exceeded. Try again later.");
                return;
            }
            _clients.TryUpdate(key, (newCount, entry.Reset), entry);
        }

        await _next(ctx);
    }
}
