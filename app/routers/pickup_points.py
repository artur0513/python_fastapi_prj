from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.models import PickupPoint
from app.schemas.schemas import PickupPointCreate, PickupPointRead, PickupPointUpdate
from app.auth.dependencies import get_current_user, require_manager

router = APIRouter(prefix="/pickup-points", tags=["Точки выдачи"])


# Получить все точки – доступно любому авторизованному
@router.get("/", response_model=List[PickupPointRead])
def list_pickup_points(
        session: Session = Depends(get_session),
        current_user=Depends(get_current_user)
):
    points = session.exec(select(PickupPoint)).all()
    return points


# Получить конкретную точку по ID
@router.get("/{point_id}", response_model=PickupPointRead)
def get_pickup_point(
        point_id: int,
        session: Session = Depends(get_session),
        current_user=Depends(get_current_user)
):
    point = session.get(PickupPoint, point_id)
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Точка не найдена")
    return point


# Создать – только менеджер
@router.post("/", response_model=PickupPointRead, status_code=status.HTTP_201_CREATED)
def create_pickup_point(
        point_in: PickupPointCreate,
        session: Session = Depends(get_session),
        current_user=Depends(require_manager)
):
    point = PickupPoint(**point_in.model_dump())
    session.add(point)
    session.commit()
    session.refresh(point)
    return point


# Обновить – только менеджер
@router.put("/{point_id}", response_model=PickupPointRead)
def update_pickup_point(
        point_id: int,
        point_in: PickupPointUpdate,
        session: Session = Depends(get_session),
        current_user=Depends(require_manager)
):
    point = session.get(PickupPoint, point_id)
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Точка не найдена")
    update_data = point_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(point, key, value)
    session.add(point)
    session.commit()
    session.refresh(point)
    return point


# Удалить – только менеджер
@router.delete("/{point_id}", status_code=status.HTTP_200_OK)
def delete_pickup_point(
        point_id: int,
        session: Session = Depends(get_session),
        current_user=Depends(require_manager)
):
    point = session.get(PickupPoint, point_id)
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Точка не найдена")
    session.delete(point)
    session.commit()
    return {"message": "Точка удалена"}
