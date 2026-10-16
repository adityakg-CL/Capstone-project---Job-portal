from fastapi import APIRouter
from controllers import admin, applications, auth, dashboard, interviews, jobs, notifications, referrals, users

api_router = APIRouter()
for controller in (auth, users, jobs, applications, referrals, interviews, notifications, admin, dashboard):
    api_router.include_router(controller.router)
