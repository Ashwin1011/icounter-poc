# Runbook — Identity Service Outage

Use this runbook when Identity Service authentication or token validation is degraded.

### Initial response
1. Check authentication error rate by cluster.
2. Determine whether failures are caused by certificates, token validation, datastore latency, or network connectivity.
3. Verify gateway behavior and cached metadata where applicable.
4. Avoid increasing global retry counts because retries can amplify load.

### Escalation
Sev-1 authentication impact requires Identity Platform and SRE. Security Engineering must be notified for certificate or credential-control failures.

### Recovery
Confirm login, token validation, and service-to-service authentication before declaring recovery.
