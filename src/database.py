from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings

DATABASE_URL = settings.get_db_url

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

engine = create_async_engine(DATABASE_URL, future=True, echo=True)
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Генератор для получения сессий
async def get_db():
    async with async_session() as db:
        yield db


