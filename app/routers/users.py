from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.schemas.schemas import UserRead, UserUpdateCoords
from app.auth.dependencies import get_current_user
from app.models.models import User

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    """Возвращает профиль текущего пользователя."""
    return current_user


@router.put("/me/coords", response_model=UserRead)
def update_my_coords(
    coords: UserUpdateCoords,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Обновляет координаты курьера (или любого пользователя)."""
    current_user.latitude = coords.latitude
    current_user.longitude = coords.longitude
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user
