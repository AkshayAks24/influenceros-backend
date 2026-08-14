from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    profile_image: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: Literal["brand", "influencer"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
