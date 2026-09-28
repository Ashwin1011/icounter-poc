# SVC-ID — Identity Service

Identity Service provides user authentication, OAuth client management, session validation, and service-to-service identity primitives.

**Owner:** Identity Platform (TEAM-ID)
**Primary products:** All three products

### Dependencies
- API Gateway relies on Identity Service for authentication metadata.
- Payment Service uses Identity Service for authenticated user context.
- Order Service uses Identity Service for authenticated user context.
- SupportHub uses Identity Service for agent authentication.

Identity Service stores identity metadata in its own datastore and publishes session-related events to Data Platform.

### Reliability notes
The service is considered a critical shared dependency. Availability targets require conservative timeouts and local caching of non-sensitive metadata. OAuth client migrations are coordinated through Project Orion.
