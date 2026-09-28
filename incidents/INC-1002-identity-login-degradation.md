# INC-1002 — Identity Login Degradation

**Date:** 2026-07-02
**Severity:** Sev-1
**Primary service:** Identity Service (SVC-ID)
**Owner team:** Identity Platform (TEAM-ID)
**Incident commander:** Hannah Brooks (SRE)

### Summary
Login and token validation requests experienced intermittent failures for 31 minutes.

### Impact
Users of CommerceCloud and SupportHub experienced login failures. API requests with already-valid cached session metadata were less affected.

### Root cause
A certificate renewal deployment introduced an invalid trust-chain configuration for one authentication cluster.

### Resolution
The deployment was rolled back and the certificate chain was corrected. Security Engineering reviewed the certificate rotation process after the incident.

### Follow-up
Project Orion added a certificate-validation step to the migration and deployment pipeline.
