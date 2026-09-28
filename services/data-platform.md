# SVC-DATA — Data Platform

Data Platform provides event ingestion, analytical storage, operational event streams, and reporting datasets.

**Owner:** Core Platform (TEAM-PLAT)
**Products:** All three products

### Dependencies
Data Platform consumes events from Payment Service, Order Service, Identity Service, Notification Service, and Customer Profile Service.

### Consumers
BillingPro reporting and operational analytics depend on Data Platform. SRE also uses Data Platform for selected incident analysis dashboards.

### Reliability notes
The platform is intentionally asynchronous. Delayed data should be labeled as stale rather than presented as real-time truth.
