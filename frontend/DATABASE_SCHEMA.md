# Database Schema Plan

This is a proposed schema inventory, not a claim that collections currently exist. Inspect the actual MongoDB database and existing code before creating collections or migrations.

| Collection | Purpose | Key fields (proposed) |
|---|---|---|
| `users` | Accounts and profiles | normalized email (unique), password hash, role, profile, status, created/updated timestamps |
| `jobs` | Internal job requisitions | title, team, location, skills, description, owner/manager IDs, `open`/`closed` status, timestamps |
| `applications` | Employee applications | job ID, employee ID, status, status history, timestamps |
| `referrals` | Referral submissions | referrer ID, job ID if applicable, candidate details, status/history, attribution fields |
| `referral_bonuses` | Bonus eligibility and payment tracking | referral ID, amount/rule reference, approval status, payment status, approver and timestamps |
| `interviews` | Interview scheduling and feedback | application ID, participants, scheduled time, status, feedback, timestamps |
| `notifications` | Persistent user notifications | recipient ID, type, message, read state, timestamp |
| `audit_logs` | Append-only security/business audit | actor ID, action, entity type/ID, outcome, timestamp, minimal change summary |
| `business_rules` | Configurable policy, if needed | rule key, value, effective dates, editor ID |

## Indexes to evaluate
- Unique index on normalized user email.
- Jobs by status/team/location and relevant search fields.
- Applications by employee, job and status; enforce duplicate-application policy where possible.
- Referrals by referrer, job and normalized candidate identifier as appropriate.
- Bonuses by referral and approval/payment status.
- Interviews by application and scheduled time.
- Notifications by recipient and read status.
- Audit logs by actor, entity and timestamp.

## Safety notes
- Define ownership and visibility rules before exposing applicant/referral data.
- Use consistent ObjectId/string conversion at API boundaries.
- Validate pagination limits and all query filters.
- Avoid destructive setup scripts; document migrations and backups.
- Exact fields, retention rules and business constraints must be confirmed against company policy.
