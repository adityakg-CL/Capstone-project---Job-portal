# Project Audit — CirrusLabs Internal Hiring Portal

## Scope inspected
The supplied archive contains a React 19 + TypeScript + Vite frontend. It does **not** contain a backend, FastAPI application, MongoDB configuration, API tests, or an existing backend repository. Therefore this audit describes only the supplied frontend; backend behavior cannot be verified.

## Current structure
- `src/App.tsx`: single-file app, screen rendering, mock data, auth screens, employee and hiring-manager views.
- `src/index.css`: styling and responsive presentation.
- `src/main.tsx`: React entry point.
- `package.json`: React, React DOM, TypeScript, Vite and Tailwind dependencies. No HTTP client or router dependency is declared.

## Findings
### Critical — demo behavior is not authentication
- Submitting the login/register form immediately navigates to the dashboard.
- The login page exposes an employee/hiring-manager demo role selector. This is not safe for a real system; the server must determine the user's role.
- No real credential validation, password hashing, JWT handling, logout endpoint, session expiry, protected route guard, or role authorization is present.
- Registration fields are not collected/validated as a structured payload. `Field` uses uncontrolled inputs and does not expose values to the parent form.

### Critical — data is hardcoded
- Job cards, dashboard statistics, recent activity, application rows, referral rows, applicant rows, profile details and referral audit history are hardcoded in `src/App.tsx`.
- Applying to a role only changes local component state.
- Referral/job forms show local success state rather than persisting records.
- Referral bonus approval/payment buttons update local UI only.
- Job search, filters, sort controls and pagination are mostly presentational and do not query/filter server data.
- Several buttons (e.g. edit/delete, view resume, save plan, change photo) have no implemented action.

### Authorization and coverage gaps
- The role type is `"employee" | "manager"`; the requested backend roles are `employee`, `hiring_manager`, and `hr_admin`.
- There is no HR/Admin workspace or admin-specific page set.
- Frontend screen state is held in a local `useState`; there is no URL-backed router, deep-link handling, or server-enforced route access.
- No centralized API client, API base URL configuration, loading/error/empty API states, or API integration map exists.
- No test scripts or test framework are configured in `package.json`.
- No `.env.example`, database schema, testing guide, or setup README is present in the archive.

## Recommended implementation order
1. Keep a clean copy of this frontend and create a separate backend project/repository boundary.
2. Agree on API contracts and business rules before wiring UI behavior.
3. Implement backend auth, secure role provisioning and authorization first.
4. Implement jobs and applications; connect employee and hiring-manager screens.
5. Implement referrals/bonuses with explicit eligibility and status-transition rules.
6. Add interviews, notifications, audit logs and HR/Admin screens.
7. Replace mock content with API-backed loading/error/empty states.
8. Add automated tests and run frontend build + backend tests against an isolated test database.

## Important business-rule decisions still needed
The supplied frontend/prompt does not define the company's real rules for referral bonus amounts, eligibility windows, duplicate referrals, who approves requisitions, who may see applicant contact details, allowed application-stage transitions, or who may mark a bonus as paid. Keep these configurable or obtain confirmation; do not treat the current mock values as policy.

## Verification status
- Source inspection: completed for the supplied frontend archive.
- Backend inspection: not possible; backend files were not supplied.
- Runtime/build/test verification: not performed in this audit. Do not treat the frontend as production-ready.
