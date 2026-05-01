from enum import Enum
from typing import Optional, List, Literal
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class RoleEnum(str, Enum):
    MANAGER = "manager"
    COURIER = "courier"


class OrderStatusEnum(str, Enum):
    NEW = "new"
    IN_DELIVERY = "in_delivery"
    DELIVERED = "delivered"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    full_name: str
    role: RoleEnum = Field(default=RoleEnum.COURIER)

    # координаты используются только для курьеров, для менеджеров могут быть None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # заказы, назначенные этому курьеру
    orders: List["Order"] = Relationship(back_populates="courier")


class PickupPoint(SQLModel, table=True):
    __tablename__ = "pickup_points"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: str
    latitude: float
    longitude: float

    # связанные заказы (откуда забирать)
    orders: List["Order"] = Relationship(back_populates="pickup_point")


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    weight: Optional[float] = None
    status: OrderStatusEnum = Field(default=OrderStatusEnum.NEW)
    delivery_latitude: float
    delivery_longitude: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # внешние ключи
    assigned_courier_id: Optional[int] = Field(default=None, foreign_key="users.id")
    pickup_point_id: int = Field(foreign_key="pickup_points.id")

    # отношения
    courier: Optional[User] = Relationship(back_populates="orders")
    pickup_point: PickupPoint = Relationship(back_populates="orders")
