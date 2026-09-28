# INC-1003 — Notification Backlog

**Date:** 2026-07-19
**Severity:** Sev-2
**Primary service:** Notification Service (SVC-NOTIFY)
**Owner team:** Customer Experience (TEAM-CX)
**Incident commander:** Mei Wong

### Summary
Notification delivery backlog increased significantly during a third-party provider slowdown.

### Impacted customers
GreenLeaf Health and several smaller SupportHub customers experienced delayed notifications. No message loss was confirmed.

### Root cause
Notification workers were configured for a normal provider response time and did not scale quickly enough when provider latency increased.

### Resolution
SRE increased worker capacity and Customer Experience temporarily reduced non-critical notification throughput.

### Follow-up
Project Apollo added provider-latency alerts and backlog-based autoscaling requirements.
