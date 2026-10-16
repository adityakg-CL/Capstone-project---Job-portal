from pydantic import BaseModel, Field, EmailStr
from typing import Literal
from datetime import datetime

class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    title: str | None = Field(default=None, max_length=120)
    team: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    skills: list[str] | None = Field(default=None, max_length=50)
    # role / is_active / id are deliberately absent: a profile edit must not be
    # able to grant privileges or change an immutable identifier.

class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

class JobStatusUpdate(BaseModel):
    status: Literal["open", "closed"]

class JobCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    team: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=120)
    employment_type: str = Field(default="Full-time", max_length=60)
    experience: str = Field(default="", max_length=100)
    salary_band: str = Field(default="", max_length=100)
    description: str = Field(min_length=20, max_length=12000)
    skills: list[str] = Field(default_factory=list, max_length=50)
class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    team: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    employment_type: str | None = Field(default=None, max_length=60)
    experience: str | None = Field(default=None, max_length=100)
    salary_band: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, min_length=20, max_length=12000)
    skills: list[str] | None = Field(default=None, max_length=50)

class ApplicationCreate(BaseModel):
    cover_note: str = Field(default="", max_length=5000)

class ApplicationStatusUpdate(BaseModel):
    status: Literal["under_review", "shortlisted", "interview", "offered", "hired", "rejected"]
    reason: str | None = Field(default=None, max_length=1000)

class ReferralCreate(BaseModel):
    candidate_name: str = Field(min_length=2, max_length=120)
    candidate_email: EmailStr
    job_id: str | None = None
    note: str = Field(default="", max_length=3000)

REFERRAL_STATUSES = ("pending", "eligible", "ineligible", "interview", "offered", "hired", "rejected")

class ReferralStatusUpdate(BaseModel):
    status: Literal["pending", "eligible", "ineligible"]
    reason: str | None = Field(default=None, max_length=1000)

class BonusDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    amount: float | None = Field(default=None, ge=0, le=100000000)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    reason: str | None = Field(default=None, max_length=1000)

class BonusPaymentUpdate(BaseModel):
    payment_status: Literal["processing", "paid", "on_hold"]
    reference: str | None = Field(default=None, max_length=200)

class InterviewCreate(BaseModel):
    application_id: str
    scheduled_at: datetime
    timezone: str = Field(default="Asia/Kolkata", max_length=80)
    participants: list[str] = Field(default_factory=list, max_length=30)
    notes: str = Field(default="", max_length=3000)

class InterviewUpdate(BaseModel):
    scheduled_at: datetime | None = None
    status: Literal["scheduled", "cancelled"] | None = None
    notes: str | None = Field(default=None, max_length=3000)

class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    feedback: str = Field(min_length=5, max_length=5000)
    recommendation: Literal["strong_yes", "yes", "mixed", "no", "strong_no"]
