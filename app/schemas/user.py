from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=120)
    target_band: float = Field(default=7.0, ge=4.0, le=9.0)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    target_band: float | None = Field(default=None, ge=4.0, le=9.0)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str | None
    target_band: float
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
