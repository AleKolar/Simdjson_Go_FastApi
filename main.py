import os
import json
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Query, Depends
from sqlalchemy import select, func, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm import Mapped, mapped_column
import aio_pika
from contextlib import asynccontextmanager
from pydantic import BaseModel




# Схема для событий
class EventRequest(BaseModel):
    platform: str
    event_name: str
    profile_id: str
    device_ip: str
    event_datetime: datetime
    raw_data: dict


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/mydatabase")


# Функция для создания базы данных
async def get_db() -> AsyncSession:
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session

    # Основное приложение


app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Подключение к RabbitMQ
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
    rabbit_connection = await aio_pika.connect_robust(rabbitmq_url)
    rabbit_channel = await rabbit_connection.channel()

    yield  # Приложение работает

    # Закрытие соединений при завершении
    await rabbit_connection.close()


app.lifespan(lifespan)


@app.post("/events")
async def create_event(event_request: EventRequest):
    data = event_request.dict()
    json_data = json.dumps(data).encode()

    # Отправка данных в очередь RabbitMQ
    await app.state.rabbit_channel.default_exchange.publish(
        aio_pika.Message(body=json_data),
        routing_key="events"
    )
    return {"status": "event queued"}


@app.get("/analytics/events")
async def get_events(
        start_time: datetime = Query(...),
        end_time: datetime = Query(...),
        event_name: str = Query(None),
        profile_id: str = Query(None),
        db: AsyncSession = Depends(get_db)
):
    query = select(Event).where(
        Event.event_datetime >= start_time,
        Event.event_datetime <= end_time
    )

    if event_name:
        query = query.where(Event.event_name == event_name)
    if profile_id:
        query = query.where(Event.profile_id == profile_id)

    result = await db.execute(query)
    return result.scalars().all()


@app.get("/analytics/stats")
async def get_stats(
        start_time: datetime,
        end_time: datetime,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(
            Event.event_name,
            func.count().label("total"),
            func.min(Event.event_datetime).label("first_occurrence"),
            func.max(Event.event_datetime).label("last_occurrence")
        ).where(
            Event.event_datetime.between(start_time, end_time)
        ).group_by(Event.event_name)
    )
    return result.all()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
