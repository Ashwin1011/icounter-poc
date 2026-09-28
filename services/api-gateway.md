# SVC-GW — API Gateway

API Gateway is the public and internal entry point for Nexora APIs.

**Owner:** Core Platform (TEAM-PLAT)
**Primary product use:** CommerceCloud, BillingPro, SupportHub

### Responsibilities
- TLS termination and request routing
- Authentication handoff to Identity Service
- Rate limiting
- Request tracing and correlation IDs
- API version routing

### Dependencies
API Gateway depends directly on Identity Service for authentication metadata and on Core Platform infrastructure for service discovery.

### Important relationships
Payment Service, Order Service, Search Service, and Customer Profile Service receive traffic through API Gateway.

### Reliability notes
The gateway is designed to fail closed for invalid authentication tokens but should avoid cascading failures when Identity Service has a temporary latency spike. Circuit-breaking and bounded timeouts are configured at the gateway layer.
