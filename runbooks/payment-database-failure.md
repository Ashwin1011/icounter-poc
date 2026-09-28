# Runbook — Payment Service Dependency Failure

Use this runbook when Payment Service cannot reliably complete authorization because a critical dependency is unavailable or degraded.

### Initial response
1. Confirm the scope using Payment Service latency and error-rate dashboards.
2. Determine whether the issue is isolated to a processor, Identity Service, Order Service, or another dependency.
3. Enable or verify circuit breakers before increasing request timeouts.
4. Avoid retries that can amplify processor or dependency load.

### Escalation
For Sev-1 impact, notify Payments Engineering and SRE immediately. Security Engineering should be engaged if payment-data handling or access controls may be involved.

### Recovery
Validate authorization success rate, p95 latency, and downstream queue health before restoring normal traffic.

### Post-incident
Create a timeline, capture the dependency failure mode, and record any configuration changes used during mitigation.
