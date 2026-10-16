# Backend Audit

The supplied source was a React 19 + TypeScript + Vite frontend. It contains no completed FastAPI backend or MongoDB integration. Its UI uses demo/local state for authentication, jobs, applications, referrals, bonus actions, profiles and dashboard values. The existing front-end role type is `employee | manager`; backend uses the intended secure roles `employee | hiring_manager | hr_admin`. The frontend's role selector is demo-only and must not be treated as authority.

The implementation maps the supplied API plan to `/api/v1` endpoints. The backend does not modify or replace the frontend. No company-specific bonus amount or eligibility policy was found in the provided task context; approval requires an explicit amount and HR-controlled eligibility.
