from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.models import RoleEnum
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[RoleEnum] = RoleEnum.COURIER  # по умолчанию курьер


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

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


class OrderCreate(BaseModel):
    description: str
    weight: Optional[float] = None
    delivery_latitude: float
    delivery_longitude: float
    pickup_point_id: int
    assigned_courier_id: int


class OrderUpdate(BaseModel):
    description: Optional[str] = None
    weight: Optional[float] = None
    status: Optional[str] = None  # можно передать "new", "in_delivery", "delivered"
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    pickup_point_id: Optional[int] = None
    assigned_courier_id: Optional[int] = None


class OrderRead(BaseModel):
    id: int
    description: str
    weight: Optional[float] = None
    status: str
    delivery_latitude: float
    delivery_longitude: float
    created_at: datetime
    pickup_point_id: int
    assigned_courier_id: Optional[int] = None

    class Config:
        from_attributes = True


class UserUpdateCoords(BaseModel):
    latitude: float
    longitude: float