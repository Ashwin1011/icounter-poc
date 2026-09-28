# Security Review Guidance

Security Engineering should be involved when a change introduces or modifies:
- Authentication or authorization logic
- Customer-data flows
- Secrets or credentials
- Certificate rotation
- Privileged production access
- Payment-data handling

For high-risk changes, the design review should identify trust boundaries, data classification, failure modes, and rollback procedures.
