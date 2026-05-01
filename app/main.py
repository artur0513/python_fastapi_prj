from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine
from sqlmodel import SQLModel

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