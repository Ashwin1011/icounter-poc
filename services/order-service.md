# SVC-ORD — Order Service

Order Service manages order creation, validation, order state transitions, and fulfillment-facing events.

**Owner:** Customer Experience (TEAM-CX)
**Products:** CommerceCloud

### Dependencies
- API Gateway (SVC-GW)
- Identity Service (SVC-ID)
- Payment Service (SVC-PAY) for payment state
- Customer Profile Service (SVC-CUST) for customer context
- Notification Service (SVC-NOTIFY) for transactional notifications

Order Service publishes order lifecycle events to Data Platform.

### Reliability notes
Payment authorization is treated as a critical synchronous dependency during checkout. Notification delivery is asynchronous and should not block order completion.
