# PROJ-MERCURY — Project Mercury

Project Mercury is a payment-performance initiative focused on reducing checkout authorization latency.

**Technical owner:** Marcus Chen
**Primary team:** Payments Engineering (TEAM-PAY)
**Status:** In progress

### Scope
- Improve processor routing
- Reduce unnecessary synchronous dependency calls
- Add latency breakdowns
- Improve timeout and circuit-breaker behavior

### Services involved
Payment Service, API Gateway, Identity Service, Order Service.

### Success metric
Reduce Payment Service p95 authorization latency by 25% without increasing authorization error rate.

### Dependency
Mercury relies on Project Atlas for standardized latency and tracing dashboards.
