from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    name: str = Field(..., min_length=1, max_length=100)
    preferred_language: str = Field(default="ru", pattern="^(kk|ru|en)$")
    currency: str = Field(default="KZT", pattern="^(KZT|USD|EUR|RUB)$")


class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    preferred_language: Optional[str] = Field(None, pattern="^(kk|ru|en)$")
    currency: Optional[str] = Field(None, pattern="^(KZT|USD|EUR|RUB)$")


class TelegramAuthData(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


class UserResponse(BaseModel):
    id: str
    email: Optional[str] = None
    name: str
    preferred_language: str
    currency: str
    role: str
    created_at: datetime
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
