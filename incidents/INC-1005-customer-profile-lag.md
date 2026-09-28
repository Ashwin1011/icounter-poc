# INC-1005 — Customer Profile Synchronization Lag

**Date:** 2026-08-23
**Severity:** Sev-2
**Primary service:** Customer Profile Service (SVC-CUST)
**Owner team:** Customer Experience (TEAM-CX)
**Incident commander:** Rohan Iyer

### Summary
Customer Profile Service consumed synchronization events from Data Platform with elevated delay for approximately 68 minutes.

### Impact
Some communication preferences were stale. No source-of-truth records were lost.

### Root cause
A consumer group was stuck after a deployment and required restart and offset verification.

### Resolution
SRE restarted affected consumers and validated event offsets before releasing the service back to normal traffic.

### Follow-up
Apollo migration gates now require profile-event freshness to remain below the agreed threshold.
