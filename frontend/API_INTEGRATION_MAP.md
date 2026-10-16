# API Integration Map

Status refers to the supplied frontend as inspected. Endpoint paths below are proposed contracts, not existing verified endpoints.

| Screen / area | Proposed API | Current state |
|---|---|---|
| Login / registration | `POST /api/auth/login`, `POST /api/auth/register` | Demo-only; no API calls |
| Logout / current user | `POST /api/auth/logout`, `GET /api/auth/me` | No session/API integration |
| Employee dashboard | `GET /api/dashboard/employee` | Hardcoded stats and activity |
| Employee profile | `GET /api/users/me`, `PATCH /api/users/me` | Hardcoded profile; form not persisted |
| Job search/details | `GET /api/jobs`, `GET /api/jobs/{job_id}` | Hardcoded jobs and controls |
| Submit application | `POST /api/jobs/{job_id}/applications` | Local state only |
| Application history | `GET /api/applications/me`, `GET /api/applications/{id}` | Hardcoded rows |
| Withdraw application | `POST /api/applications/{id}/withdraw` | Not implemented |
| Submit referral | `POST /api/referrals` | Local success state only |
| Employee referrals | `GET /api/referrals/me` | Hardcoded rows |
| Referral/bonus details | `GET /api/referrals/{id}`, `GET /api/referral-bonuses/me` | Hardcoded history/status |
| Hiring manager dashboard | `GET /api/dashboard/hiring-manager` | Hardcoded |
| Create/edit jobs | `POST /api/jobs`, `PATCH /api/jobs/{id}` | Local-only form |
| Manage jobs | `GET /api/jobs/managed` | Hardcoded rows |
| Applicants/review | `GET /api/jobs/{id}/applications`, `PATCH /api/applications/{id}/status` | Hardcoded rows; actions incomplete |
| Interviews | `POST /api/interviews`, `PATCH /api/interviews/{id}` | No interview workflow in current UI |
| Bonus approval/payment status | `PATCH /api/referral-bonuses/{id}/decision`, `PATCH /api/referral-bonuses/{id}/payment-status` | Local-only UI state |
| Notifications | `GET /api/notifications`, `PATCH /api/notifications/{id}/read` | No notification integration |
| HR/Admin | `/api/admin/*` endpoints with backend role checks | Pages not present |
| Audit history | `GET /api/admin/audit-logs` | Not present |

## Integration verification
No endpoint above has been verified against a backend because no backend source or running service was included. Update this table with actual request/response contracts and test results after implementation.
