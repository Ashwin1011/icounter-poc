# PROJ-ORION — Project Orion

Project Orion migrates legacy OAuth clients to Identity Service.

**Technical owner:** Daniel Ortiz
**Primary team:** Identity Platform (TEAM-ID)
**Status:** In progress

### Scope
- Migrate legacy OAuth clients
- Standardize token validation
- Retire duplicate authentication libraries

### Services involved
Identity Service and API Gateway.

### Dependencies
Orion requires API Gateway compatibility changes before legacy clients are switched. Security Engineering must approve high-risk authentication changes.

### Success criteria
All participating clients use the standard Identity Service flow and legacy credential validation paths are disabled.
