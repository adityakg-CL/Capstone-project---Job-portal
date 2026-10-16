# Backend Implementation Plan and Current Scope

1. Configuration, MongoDB connection, safe index initialization, health endpoint.
2. Email/password authentication, JWT bearer/cookie support, token-version logout invalidation, role dependencies.
3. Profiles, open/closed job management, applications and status history.
4. Referrals, HR eligibility decision, bonus approval/payment tracking.
5. Interviews, feedback, persistent notifications, HR dashboard and audit log APIs.
6. Pytest tests and API/schema documentation.

This is a first backend implementation scaffold, not a claim of production certification. The environment must provide MongoDB and a configured secret. Workflow rules not established by source are intentionally explicit or conservative.
