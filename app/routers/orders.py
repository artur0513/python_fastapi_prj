from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.models import Order, PickupPoint, User, RoleEnum, OrderStatusEnum
from app.schemas.schemas import OrderCreate, OrderRead, OrderUpdate
from app.auth.dependencies import get_current_user, require_manager

router = APIRouter(prefix="/orders", tags=["Заказы"])


# Вспомогательная функция проверки существования точки и курьера
def validate_order_dependencies(order_data, session):
    # Проверка существования точки выдачи
    point = session.get(PickupPoint, order_data.pickup_point_id)
    if not point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Точка выдачи с id {order_data.pickup_point_id} не найдена"
        )
    # Проверка существования и роли курьера
    courier = session.get(User, order_data.assigned_courier_id)
    if not courier or courier.role != RoleEnum.COURIER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Назначенный пользователь не является курьером или не существует"
        )


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
        order_in: OrderCreate,
        session: Session = Depends(get_session),
        current_user=Depends(require_manager)
):
    validate_order_dependencies(order_in, session)
    order = Order(
        description=order_in.description,
        weight=order_in.weight,
        status=OrderStatusEnum.NEW,
        delivery_latitude=order_in.delivery_latitude,
        delivery_longitude=order_in.delivery_longitude,
        pickup_point_id=order_in.pickup_point_id,
        assigned_courier_id=order_in.assigned_courier_id,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


@router.get("/", response_model=List[OrderRead])
def list_orders(
        status_filter: Optional[str] = Query(None, alias="status"),
        courier_id: Optional[int] = None,
        session: Session = Depends(get_session),
        current_user=Depends(get_current_user)
):
    query = select(Order)
    if status_filter:
        query = query.where(Order.status == status_filter)
    if courier_id:
        query = query.where(Order.assigned_courier_id == courier_id)
    orders = session.exec(query).all()
    return orders


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
        order_id: int,
        session: Session = Depends(get_session),
        current_user=Depends(get_current_user)
):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    return order


@router.put("/{order_id}", response_model=OrderRead)
def update_order(
        order_id: int,
        order_in: OrderUpdate,
        session: Session = Depends(get_session),
        current_user=Depends(require_manager)
):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")

    update_data = order_in.model_dump(exclude_unset=True)

    # Если меняются pickup_point_id или assigned_courier_id, проверяем их
    if "pickup_point_id" in update_data or "assigned_courier_id" in update_data:
        # Собираем временный объект для проверки (используем старые значения, если новых нет)
        temp_pickup = update_data.get("pickup_point_id", order.pickup_point_id)
        temp_courier = update_data.get("assigned_courier_id", order.assigned_courier_id)
        # Валидируем через вспомогательную функцию
        validate_order_dependencies(
            OrderCreate(
                description="tmp",
                delivery_latitude=0.0,
                delivery_longitude=0.0,
                pickup_point_id=temp_pickup,
                assigned_courier_id=temp_courier
            ),
            session
        )

    # Применяем изменения
    for key, value in update_data.items():
        setattr(order, key, value)

    session.add(order)
    session.commit()
    session.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_200_OK)
def delete_order(
        order_id: int,
        session: Session = Depends(get_session),
        current_user=Depends(require_manager)
):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    session.delete(order)
    session.commit()
    return {"message": "Заказ удалён"}
