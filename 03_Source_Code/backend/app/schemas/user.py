from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional
from app.models.user import UserRole

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    nim: str
    phone: str
    password: str = Field(..., max_length=72)

    @validator("email")
    def validate_ipb_email(cls, v):
        if not v.endswith("@apps.ipb.ac.id"):
            raise ValueError("Email harus menggunakan domain @apps.ipb.ac.id")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    nim: str
    phone: str
    role: UserRole
    is_verified: bool

    class Config:
        from_attributes = True

class UserLoginResponse(BaseModel):
    """Response login: data user + token, sesuai kontrak FE authStore."""
    id: int
    name: str
    email: str
    nim: str
    phone: str
    role: UserRole
    is_verified: bool
    token: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., max_length=72)
