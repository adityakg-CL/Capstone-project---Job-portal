# Testing and Verification

## Current state
The supplied frontend archive has no test script or configured test framework in `package.json`. No backend was supplied. No test results are claimed by this document.

## Required checks before release
### Authentication
- Valid login, invalid password, unknown account, logout and expired/invalid JWT.
- Registration restrictions and rejection of client-supplied elevated roles.
- Login throttling and safe error messages.
- First HR/Admin provisioning process.

### Authorization / privacy
- Employee cannot read/update another employee's applications, referrals, bonuses or notifications.
- Hiring manager can only manage authorized requisitions and their applicant records.
- Hiring managers can only open/close their own jobs; only HR/Admin can approve bonuses or change roles.
- Unauthorized and forbidden requests return correct status codes.

### Workflows
- Job creation, Open/Closed status changes, and All Jobs/Open/Closed filters.
- Cannot apply to closed jobs; duplicate behavior matches documented policy.
- Application stage transitions are validated and audited.
- Referral duplicates/ownership/eligibility and bonus calculations follow confirmed business rules.
- Bonus approval and payment status are distinct; payment tracking does not transfer money.
- Interview schedule/reschedule/cancel and feedback permissions.
- Notifications and audit events are created on expected actions.

### Frontend
- `npm run build`.
- Test form validation, loading/empty/error/success states and session expiry.
- Verify no production screen silently uses mock data.
- Verify responsive layouts and role-specific navigation.

### Environment
- Use an isolated test MongoDB database and test credentials.
- Never run destructive tests against production.
- Record exact commands, environment dependencies and pass/fail counts after running tests.
