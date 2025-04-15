from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from typing import AsyncGenerator

from src.config import settings

DATABASE_URL = settings.get_db_url()

engine = create_async_engine(DATABASE_URL)
new_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with new_session() as session:
        yield session

