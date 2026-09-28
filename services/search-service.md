# SVC-SEARCH — Search Service

Search Service indexes product and operational data to support search experiences in CommerceCloud and SupportHub.

**Owner:** Core Platform (TEAM-PLAT)
**Products:** CommerceCloud and SupportHub

### Dependencies
- API Gateway for request ingress
- Data Platform for source events
- Core Platform indexing infrastructure

Search is eventually consistent. A delayed indexing pipeline should not be treated as data loss unless source events are missing.

Incident INC-1004 was caused by an indexing worker regression that increased processing time.
