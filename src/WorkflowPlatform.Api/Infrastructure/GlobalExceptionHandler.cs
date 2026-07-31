using System.Net.Mime;
using Microsoft.AspNetCore.Diagnostics;

namespace WorkflowPlatform.Api.Infrastructure;

public sealed class GlobalExceptionHandler : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(
        HttpContext ctx, Exception ex, CancellationToken ct)
    {
        var (status, title) = ex switch
        {
            InvalidOperationException => (StatusCodes.Status409Conflict, "Conflict"),
            ArgumentException => (StatusCodes.Status400BadRequest, "Bad Request"),
            _ => (StatusCodes.Status500InternalServerError, "Internal Server Error")
        };

        ctx.Response.StatusCode = status;
        ctx.Response.ContentType = MediaTypeNames.Application.ProblemJson;

        await ctx.Response.WriteAsJsonAsync(new
        {
            type = $"https://tools.ietf.org/html/rfc9110#section-15.5.{status - 200}",
            title,
            status,
            detail = ex.Message,
            traceId = ctx.TraceIdentifier
        }, ct);

        return true;
    }
}
