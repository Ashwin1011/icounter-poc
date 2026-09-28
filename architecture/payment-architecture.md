# Architecture — Payment Flow

A typical CommerceCloud checkout flow is:

```text
Client -> API Gateway -> Identity Service
                     -> Order Service
                     -> Payment Service -> Processor
```

Payment Service validates request context, loads order state, selects a processor route, and performs authorization.

Payment Service must not persist raw card numbers. Tokenized payment references are used instead.

Latency can increase when Payment Service makes synchronous calls to degraded dependencies. Project Mercury is intended to reduce these dependency calls and improve circuit-breaker behavior.
