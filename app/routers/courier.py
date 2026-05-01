from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.auth.dependencies import get_current_user, require_courier
from app.models.models import User, Order, OrderStatusEnum
from app.services.route_service import build_route

router = APIRouter(prefix="/courier", tags=["Курьер"])


@router.get("/route")
def get_route(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_courier)
):
    """Возвращает оптимальный маршрут объезда всех активных заказов курьера."""
    try:
        result = build_route(session, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/complete-order/{order_id}")
def complete_order(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_courier)
):
    """Отмечает заказ доставленным (только если он принадлежит курьеру и в статусе in_delivery)."""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    if order.assigned_courier_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Это не ваш заказ")
    if order.status != OrderStatusEnum.IN_DELIVERY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заказ нельзя завершить: он не в статусе 'in_delivery'"
        )
    order.status = OrderStatusEnum.DELIVERED
    session.add(order)
    session.commit()
    return {"message": f"Заказ {order_id} доставлен"}
