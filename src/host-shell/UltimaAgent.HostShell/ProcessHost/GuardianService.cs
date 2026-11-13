namespace UltimaAgent.HostShell.ProcessHost;

internal sealed class GuardianService
{
    public static readonly TimeSpan CheckInterval = TimeSpan.FromSeconds(20);
    public static readonly TimeSpan LaunchSettleDelay = TimeSpan.FromSeconds(3);
    public static readonly TimeSpan Cooldown = TimeSpan.FromSeconds(300);
    public const int LaunchFailLimit = 3;

    private readonly IReadinessProbe _probe;
    private readonly HostTaskRegistry _registry;
    private readonly object _sync = new();
    private CancellationTokenSource? _cancellation;
    private Task? _loop;

    public GuardianService(IReadinessProbe probe, HostTaskRegistry registry)
    {
        _probe = probe;
        _registry = registry;
    }

    public void Start(CancellationToken cancellationToken)
    {
        lock (_sync)
        {
            if (_loop is not null)
            {
                throw new InvalidOperationException("GuardianService is already running.");
            }
            _cancellation = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            _loop = RunAsync(_cancellation.Token);
        }
    }

    public async Task StopAsync()
    {
        Task? loop;
        lock (_sync)
        {
            _cancellation?.Cancel();
            loop = _loop;
        }
        if (loop is not null)
        {
            try
            {
                await loop.ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
            }
        }
        lock (_sync)
        {
            _cancellation?.Dispose();
            _cancellation = null;
            _loop = null;
        }
    }

    private async Task RunAsync(CancellationToken cancellationToken)
    {
        const string taskId = "agent-server";
        int failedLaunches = 0;
        DateTimeOffset? cooldownUntil = null;
        await _registry.AppendEventAsync(
            taskId,
            "guardian_started",
            "health=http://127.0.0.1:8756/health interval=20 fail_limit=3 cooldown=300",
            cancellationToken).ConfigureAwait(false);

        while (true)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (!_registry.IsEnabled(taskId))
            {
                await _registry.AppendEventAsync(taskId, "disabled_skip", "guardian restart disabled", cancellationToken)
                    .ConfigureAwait(false);
                await Task.Delay(CheckInterval, cancellationToken).ConfigureAwait(false);
                continue;
            }

            DateTimeOffset now = DateTimeOffset.Now;
            if (cooldownUntil is DateTimeOffset until && now < until)
            {
                await Task.Delay(CheckInterval, cancellationToken).ConfigureAwait(false);
                continue;
            }
            if (cooldownUntil is not null)
            {
                failedLaunches = 0;
                cooldownUntil = null;
                await _registry.AppendEventAsync(taskId, "cooldown_ended", "launch failure count reset", cancellationToken)
                    .ConfigureAwait(false);
            }

            bool healthy = await _probe.IsAgentReadyAsync(cancellationToken).ConfigureAwait(false);
            await _registry.RecordProbeAsync(
                taskId,
                healthy,
                healthy ? "health endpoint ready" : "health endpoint unavailable",
                cancellationToken).ConfigureAwait(false);
            if (healthy)
            {
                failedLaunches = 0;
                await Task.Delay(CheckInterval, cancellationToken).ConfigureAwait(false);
                continue;
            }

            bool recovered = false;
            string failureDetail;
            try
            {
                int processId = await _registry.RestartAsync(taskId, "guardian health failure", cancellationToken)
                    .ConfigureAwait(false);
                await Task.Delay(LaunchSettleDelay, cancellationToken).ConfigureAwait(false);
                recovered = await _probe.IsAgentReadyAsync(cancellationToken).ConfigureAwait(false);
                failureDetail = recovered
                    ? $"health restored pid={processId}"
                    : $"health not ready after launch pid={processId}";
            }
            catch (Exception exception) when (exception is not OperationCanceledException)
            {
                failureDetail = $"launch exception={exception.GetType().Name}";
            }

            await _registry.RecordProbeAsync(taskId, recovered, failureDetail, cancellationToken)
                .ConfigureAwait(false);
            if (recovered)
            {
                failedLaunches = 0;
            }
            else
            {
                failedLaunches++;
                await _registry.AppendEventAsync(
                    taskId,
                    "restart_failed",
                    $"failure_count={failedLaunches} detail={failureDetail}",
                    cancellationToken).ConfigureAwait(false);
                if (failedLaunches >= LaunchFailLimit)
                {
                    cooldownUntil = DateTimeOffset.Now.Add(Cooldown);
                    await _registry.RecordCooldownAsync(
                        taskId,
                        cooldownUntil.Value,
                        $"failure_count={failedLaunches} cooldown_seconds=300",
                        cancellationToken).ConfigureAwait(false);
                }
            }

            await Task.Delay(CheckInterval, cancellationToken).ConfigureAwait(false);
        }
    }
}
