# SVC-NOTIFY — Notification Service

Notification Service sends email, SMS, and in-product notifications for customer and internal workflows.

**Owner:** Customer Experience (TEAM-CX)
**Products:** CommerceCloud and SupportHub

### Dependencies
- API Gateway for internal API access
- Customer Profile Service for communication preferences
- Data Platform for delivery analytics

Project Apollo is migrating legacy notification flows from product-specific implementations into this shared service.

### Reliability notes
Notification delivery uses queues. A provider slowdown should increase backlog without blocking upstream business transactions. Incident INC-1003 was caused by queue-worker capacity being insufficient during a provider slowdown.
