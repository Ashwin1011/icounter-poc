# SVC-CUST — Customer Profile Service

Customer Profile Service stores customer preferences, profile attributes, and communication settings used by downstream services.

**Owner:** Customer Experience (TEAM-CX)
**Products:** All three products

### Dependencies
- Identity Service for authenticated access
- Data Platform for profile synchronization events
- API Gateway for API access

Order Service and Notification Service consume customer profile information.

Incident INC-1005 involved delayed synchronization between Profile Service and Data Platform. The issue caused stale preferences but did not delete source-of-truth records.
