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


class PickupPointCreate(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float


class PickupPointUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PickupPointRead(BaseModel):
    id: int
    name: str
    address: str
    latitude: float
    longitude: float

    class Config:
        from_attributes = True
