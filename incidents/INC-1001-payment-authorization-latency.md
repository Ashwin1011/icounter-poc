# INC-1001 — Payment Authorization Latency

**Date:** 2026-06-14
**Severity:** Sev-1
**Primary service:** Payment Service (SVC-PAY)
**Owner team:** Payments Engineering (TEAM-PAY)
**Incident commander:** Sameer Kulkarni (SRE)

### Summary
Payment authorization p95 latency increased from approximately 1.2 seconds to 4.8 seconds for 47 minutes. Checkout conversion dropped for a subset of customers.

### Impacted customers
Northstar Retail and BluePeak Travel were directly observed in the affected traffic sample. Other CommerceCloud customers experienced elevated latency but remained below the customer-specific alert threshold.

### Root cause
A processor-routing configuration increased synchronous dependency calls during a processor degradation event. The additional calls amplified latency through Payment Service.

### Resolution
Payments Engineering reverted the routing configuration and SRE adjusted the circuit-breaker threshold. Latency returned to baseline within 12 minutes after rollback.

### Follow-up
Project Mercury was updated to reduce synchronous dependency calls and add processor-specific latency controls.
