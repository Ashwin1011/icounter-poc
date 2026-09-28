# PROJ-APOLLO — Project Apollo

Project Apollo is a customer-notification modernization initiative.

**Executive sponsor:** Rohan Iyer
**Technical owner:** Mei Wong
**Primary team:** Customer Experience (TEAM-CX)
**Status:** In progress

### Scope
- Migrate legacy notification workflows to Notification Service.
- Standardize customer communication preferences through Customer Profile Service.
- Improve observability of notification delivery.

### Services involved
Notification Service, Customer Profile Service, API Gateway.

### Dependencies
Apollo depends on Project Atlas observability standards for new dashboards and on Identity Service for authenticated administrative workflows.

### Known risk
If Customer Profile Service returns stale communication preferences, notifications may be sent using outdated settings. The project therefore requires preference freshness metrics before each migration stage.
