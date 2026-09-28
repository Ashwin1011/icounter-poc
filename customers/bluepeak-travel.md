# CUST-BLUEPEAK — BluePeak Travel

BluePeak Travel uses BillingPro for subscription billing and recurring payment collection.

### Products
BillingPro

### Important services
API Gateway, Identity Service, Payment Service, Data Platform.

### Operational notes
Billing data freshness is important for finance reporting. Delayed Data Platform ingestion may affect dashboards without affecting payment authorization itself.

### Related incidents
INC-1001 created elevated authorization latency that was visible in some BluePeak payment attempts.
