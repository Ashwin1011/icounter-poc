# INC-1004 — Search Indexing Delay

**Date:** 2026-08-05
**Severity:** Sev-2
**Primary service:** Search Service (SVC-SEARCH)
**Owner team:** Core Platform (TEAM-PLAT)
**Incident commander:** Sofia Alvarez

### Summary
Search indexing lag increased to more than four hours.

### Impacted customers
Redwood Outfitters experienced stale product-search results. SupportHub search users also saw delayed updates.

### Root cause
A worker regression increased document processing time after a search schema change.

### Resolution
The worker was rolled back, queued events were processed, and search lag returned to normal.

### Follow-up
Project Atlas added processing-time dashboards and queue-age alerts for the indexing pipeline.
