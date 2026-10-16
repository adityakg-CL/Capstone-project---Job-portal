# Testing

Run `pytest -q` from the backend directory. The included tests cover security primitives, application transitions, job creation/listing/open-close behavior, ownership and role checks, and legacy job-status migration using isolated in-memory collection fakes. They do not require or validate a live MongoDB deployment.

Before production, add isolated integration tests for registration/login/logout, ownership and role boundaries, open/closed job lifecycle and startup migration against a dedicated MongoDB test database, application duplicate/status transitions, referral duplicate/ownership, bonus approval/payment, interview permissions, notification privacy and audit logging. Never run tests against production data.
