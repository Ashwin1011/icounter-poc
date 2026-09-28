# INC-1006 — API Gateway Certificate Renewal Failure

**Date:** 2026-09-03
**Severity:** Sev-1
**Primary service:** API Gateway (SVC-GW)
**Owner team:** Core Platform (TEAM-PLAT)
**Incident commander:** Sameer Kulkarni (SRE)

### Summary
A production certificate renewal failed for one API Gateway cluster, causing TLS handshake failures for a subset of requests.

### Impact
CommerceCloud and BillingPro traffic routed through the affected cluster saw elevated request failures. Requests routed through the healthy clusters were unaffected.

### Root cause
The certificate automation pipeline accepted a certificate bundle with an incomplete intermediate chain.

### Resolution
Core Platform deployed the corrected certificate bundle and temporarily disabled automated rotation for the affected cluster pending validation.

### Follow-up
Security Engineering added a certificate-chain validation requirement to the production access and change checklist.
