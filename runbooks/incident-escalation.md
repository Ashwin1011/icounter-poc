# Runbook — Incident Escalation

### Severity guidance
- **Sev-1:** Major customer or business impact, or critical platform unavailability. SRE provides incident command unless explicitly reassigned.
- **Sev-2:** Significant degradation with meaningful but bounded impact.
- **Sev-3:** Limited impact or low-risk operational issue.

### Escalation
The service-owning team is paged first. SRE joins for Sev-1 and Sev-2 incidents. Security Engineering joins when authentication, authorization, secrets, certificates, or customer-data controls are implicated.

### Incident communication
The incident commander establishes a timeline, records decisions, assigns action owners, and ensures the final status is communicated to stakeholders.
