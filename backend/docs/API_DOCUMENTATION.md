# API Documentation

Interactive OpenAPI docs: `/docs`; schema: `/openapi.json`. All routes are under `/api/v1`.

Auth: `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`. Registration only creates `employee`; it never accepts a role. `POST /auth/refresh` intentionally returns 501 because refresh tokens are not enabled.

Profile: `GET /users/me`, `PATCH /users/me`. HR user admin: `GET /admin/users`, `PATCH /admin/users/{user_id}/role`.

Jobs: `GET /jobs`, `GET /jobs/{job_id}`, `GET /jobs/managed`, `POST /jobs`, `PATCH /jobs/{job_id}`, `PATCH /jobs/{job_id}/status`.

Jobs start as `open`; hiring managers can set their own jobs to `open` or `closed` through the status endpoint, while HR admins can act on any job. Legacy `active` and `published` statuses migrate to `open`; all other noncanonical statuses migrate to `closed` at startup. Employees can browse, apply to, and refer candidates to open jobs only.

Applications: `POST /jobs/{job_id}/applications`, `GET /applications/me`, `GET /applications/{application_id}`, `POST /applications/{application_id}/withdraw`, `GET /jobs/{job_id}/applications`, `PATCH /applications/{application_id}/status`.

Referrals/bonuses: `POST /referrals`, `GET /referrals/me`, `GET /admin/referrals`, `POST /admin/referrals/{referral_id}/eligibility`, `POST /admin/referrals/{referral_id}/bonus-decision`, `PATCH /admin/bonuses/{bonus_id}/payment`, `GET /referral-bonuses/me`.

Interviews: `POST /interviews`, `GET /interviews`, `PATCH /interviews/{interview_id}`, `POST /interviews/{interview_id}/feedback`.

Notifications: `GET /notifications`, `PATCH /notifications/{notification_id}/read`, `POST /notifications/read-all`.

Dashboards: `GET /dashboard/employee`, `GET /dashboard/hiring-manager`. HR/Admin: `GET /admin/dashboard`, `GET /admin/audit-logs`.

Authentication accepts `Authorization: Bearer <token>` or an HTTP-only `access_token` cookie. Login returns a bearer token and also sets the cookie. If cookies are used cross-site, configure secure cookies and implement a CSRF strategy before production deployment. CORS is restricted to `ALLOWED_ORIGINS`.

Role policy: employees access their own applications/referrals/notifications; hiring managers manage their own jobs and associated applications; HR admins manage roles, administer referral eligibility/bonuses, and read audit logs. Job status changes remain limited to hiring managers (their own jobs) and HR admins (any job). Validate exact endpoint schemas in `/docs`.
