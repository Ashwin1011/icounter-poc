# Architecture — Nexora Platform Overview

Nexora's customer-facing architecture uses API Gateway as the common ingress layer.

```text
Clients
  -> API Gateway
      -> Identity Service
      -> Order Service
      -> Payment Service
      -> Customer Profile Service
      -> Search Service
      -> Notification Service

Application services -> Data Platform -> analytics/reporting
```

Identity Service is a shared dependency for authenticated workflows. Payment Service and Order Service are synchronous during checkout. Notification Service and Data Platform are primarily asynchronous.

The architecture uses bounded timeouts, circuit breakers, and queue-based processing to limit failure propagation.
