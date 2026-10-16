# Implementation Plan — CirrusLabs Internal Hiring Portal

## Guardrails
- Do not implement SSO, Microsoft Entra ID, OIDC, OAuth, or Microsoft 365 authentication.
- Preserve the existing Figma-generated React/Vite UI; make only necessary UI additions.
- Use FastAPI + Pydantic + PyMongo + MongoDB for the backend unless an existing, working equivalent is later supplied.
- The backend is the authority for user identity, roles, permissions, and workflow transitions.
- Never use the current demo role selector or mock UI state as production authorization.

## Stage 0 — Repository and contract
- [x] Audit the supplied frontend.
- [ ] Obtain/inspect the existing backend (not included in supplied archive).
- [ ] Confirm referral, bonus, open/closed job and application workflow rules.
- [ ] Agree API payloads, error shape, pagination conventions and auth transport.

## Stage 1 — Authentication and user roles
- Email/password login/logout and permitted registration.
- Argon2/bcrypt password hashes; JWT expiry/signature validation.
- Secure cookie + CSRF strategy or carefully implemented bearer-token strategy.
- `/auth/me` and profile APIs.
- Server-side role checks for `employee`, `hiring_manager`, `hr_admin`.
- Safe first-admin provisioning, login throttling and audit events.
- Frontend session bootstrap, protected views and expired-session handling.

## Stage 2 — Jobs and applications
- Job requisitions with open/closed status and manager-controlled transitions.
- Employee search/filter/sort/pagination of open jobs.
- Apply, duplicate prevention, application history, status timeline and permitted withdrawal.
- Hiring-manager applicant lists, review, valid stage changes and hiring decisions.
- Persist notifications and audit records for important events.

## Stage 3 — Referrals and bonuses
- Referral submission, attribution, duplicate checks and status history.
- Configurable eligibility/bonus rules; no assumptions based on mock amounts.
- HR/Admin approval/rejection and payment-status tracking (not a payment gateway).
- Ownership checks and notifications.

## Stage 4 — Interviews, HR/Admin, notifications, audit
- Interview scheduling, rescheduling/cancellation, feedback and recommendations.
- HR/Admin dashboard, bonus approvals, payment tracking, user/role administration and audit history.
- Append-only audit records with minimal change summaries.

## Stage 5 — Frontend integration
- Add a centralized API client using a configured backend URL.
- Replace each hardcoded dataset and local-only mutation with API calls.
- Implement loading, empty, validation, success and failure states.
- Add missing pages using the existing design system.
- Keep mock data restricted to an explicit development/demo mode, never a silent production fallback.

## Stage 6 — Verification and handoff
- Unit/integration tests for authentication, authorization and each workflow.
- Isolated test database; no destructive tests against production data.
- Frontend tests and production build.
- Update setup, schema, API map and test documentation with actual outcomes.

## Blocker
Only the frontend archive and the implementation prompt were supplied. Full-stack implementation and claims of working API/database behavior require the backend repository and a configured test environment. Until then, only the frontend audit and planning can be completed honestly.
