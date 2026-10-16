from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Literal

class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class UserOut(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: Literal["employee", "hiring_manager", "hr_admin"]
    title: str | None = None
    team: str | None = None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
