from sqlmodel import create_engine, Session
from app.config import settings

# движок
engine = create_engine(settings.database_url, echo=False)  # echo=True для отладки

def get_session():
    with Session(engine) as session:
        yield session
