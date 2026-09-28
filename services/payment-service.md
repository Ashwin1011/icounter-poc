# SVC-PAY — Payment Service

Payment Service handles authorization, capture, refunds, payment-method tokenization, and processor routing.

**Owner:** Payments Engineering (TEAM-PAY)
**Products:** BillingPro and CommerceCloud

### Dependencies
- Identity Service (SVC-ID) for authenticated request context
- API Gateway (SVC-GW) for ingress
- Order Service (SVC-ORD) for order state
- Data Platform (SVC-DATA) for analytics and operational events

Payment Service integrates with external payment processors through a processor adapter layer.

### Important design rule
Cardholder data is tokenized before it enters Nexora application persistence. Application services should never persist raw card numbers.

### Current initiatives
Project Mercury focuses on reducing p95 authorization latency by improving processor routing and reducing unnecessary synchronous calls to dependent services.
