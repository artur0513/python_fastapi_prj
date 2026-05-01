from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.models import RoleEnum


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[RoleEnum] = RoleEnum.COURIER  # по умолчанию курьер


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: RoleEnum

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
