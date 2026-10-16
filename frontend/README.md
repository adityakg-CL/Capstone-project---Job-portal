# CirrusLabs TalentHub — Frontend

This repository is the supplied Figma-generated React/Vite frontend for an internal employee hiring and referral portal.

## Important current limitation
This archive contains the frontend only. It does not include the FastAPI backend or a configured MongoDB database. Current screens use hardcoded example data and local component state; they are not production-connected.

## Requirements
- Node.js compatible with the Vite version in `package.json`
- pnpm (lockfile supplied) or npm
- A separately configured backend when API integration is implemented

## Run the frontend
```bash
pnpm install
pnpm dev
```

To build:
```bash
pnpm build
```

Build/test results must be recorded after running the commands in the actual environment.

## Environment
When API integration is added, configure the backend origin using a Vite public environment variable such as `VITE_API_BASE_URL`. Do not place secrets in Vite variables; anything prefixed with `VITE_` is exposed to the browser.

## Documentation
- `PROJECT_AUDIT.md` — findings from the supplied frontend
- `IMPLEMENTATION_PLAN.md` — staged implementation plan and blocker
- `DATABASE_SCHEMA.md` — proposed MongoDB schema inventory
- `API_INTEGRATION_MAP.md` — proposed endpoint mapping and current UI status
- `TESTING.md` — required verification plan

## Authentication policy
Use standard email/password authentication with secure password hashing and JWT validation in the backend. Do not implement SSO, Microsoft Entra ID, OIDC, OAuth, or Microsoft 365 authentication. Never trust a role supplied by the browser.
