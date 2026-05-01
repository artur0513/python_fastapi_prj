from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine
from sqlmodel import SQLModel
from app.routers import auth, pickup_points, orders, users, courier


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Служба доставки",
    description="REST-сервис для управления заказами и построения оптимального маршрута для курьеров",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(pickup_points.router)
app.include_router(orders.router)
app.include_router(users.router)
app.include_router(courier.router)