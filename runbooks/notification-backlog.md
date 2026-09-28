# Runbook — Notification Backlog

Use this runbook for sustained Notification Service backlog growth.

### Response
- Check provider latency and error rates.
- Check worker concurrency and queue age.
- Scale workers when backlog growth is driven by external-provider latency.
- Preserve capacity for security and transactional notifications.
- Do not block upstream order processing unless the incident specifically affects a synchronous dependency.

### Recovery criteria
Queue age should return below the normal operational threshold and failed messages should be accounted for.
