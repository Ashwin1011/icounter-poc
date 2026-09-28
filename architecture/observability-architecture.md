# Architecture — Observability Standard

Project Atlas defines common observability patterns across services.

Every customer-facing service should emit:
- Correlation IDs
- Request latency metrics
- Error-rate metrics
- Dependency latency metrics
- Structured logs

SRE consumes these signals for incident response.

Atlas dashboards are expected to show both application health and dependency health so that teams can distinguish primary failures from cascading symptoms.
