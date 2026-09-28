# Architecture — Identity Flow

Identity Service provides authentication and token validation for customer-facing and administrative requests.

API Gateway delegates authentication metadata checks to Identity Service. Product services receive authenticated identity context after gateway validation.

SupportHub, CommerceCloud, and BillingPro all depend on this shared authentication path.

Project Orion is migrating legacy OAuth clients to this architecture.
