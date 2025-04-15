import os
import json
from contextlib import asynccontextmanager
from datetime import datetime
import aio_pika
import uvicorn
from fastapi import FastAPI, Query, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from pydantic import BaseModel

from src.ORM_models import EventIncomingORM
from src.database import get_db

# Настройки окружения
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672/")  # Явный IP
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")  # Явный IP
QUEUE_NAME = "events"


class EventCreateSchema(BaseModel):
    event_name: str
    event_datetime: datetime
    profile_id: str
    device_ip: str
    raw_data: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения с безопасной инициализацией"""
    app.state.rabbit_ready = False
    app.state.redis_ready = False

    # Инициализация RabbitMQ
    try:
        rabbit_conn = await aio_pika.connect_robust(
            RABBITMQ_URL,
            timeout=10
        )
        app.state.rabbit_channel = await rabbit_conn.channel()
        await app.state.rabbit_channel.declare_queue(QUEUE_NAME, durable=True)
        app.state.rabbit_ready = True
        print("✅ RabbitMQ подключен успешно")
    except Exception as e:
        print(f"⚠️ Ошибка RabbitMQ: {str(e)}")
        app.state.rabbit_channel = None

    # Инициализация Redis
    try:
        app.state.redis = Redis.from_url(
            REDIS_URL,
            socket_connect_timeout=5,
            socket_keepalive=True,
            decode_responses=True
        )
        if await app.state.redis.ping():
            app.state.redis_ready = True
            print("✅ Redis подключен успешно")
    except RedisConnectionError as e:
        print(f"⚠️ Ошибка Redis: {str(e)}")
        app.state.redis = None

    yield  # Здесь работает приложение

    # Корректное закрытие подключений
    if hasattr(app.state, 'rabbit_channel') and app.state.rabbit_channel:
        await app.state.rabbit_channel.close()
    if hasattr(app.state, 'redis') and app.state.redis:
        await app.state.redis.aclose()


app = FastAPI(docs_url=None, redoc_url=None, lifespan=lifespan)


@app.post("/events")
async def create_event(
        event: EventCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    """Обработка входящих событий"""
    try:
        # 1. Сохранение в БД
        event_id = 1  # Заглушка - замените на реальный код

        # 2. Отправка в RabbitMQ (если доступен)
        if app.state.rabbit_ready:
            try:
                message = aio_pika.Message(
                    body=json.dumps(event.dict()).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                )
                await app.state.rabbit_channel.default_exchange.publish(
                    message,
                    routing_key=QUEUE_NAME
                )
            except Exception as e:
                print(f"⚠️ Ошибка отправки в RabbitMQ: {str(e)}")

        # 3. Кэширование в Redis (если доступен)
        if app.state.redis_ready:
            try:
                await app.state.redis.set(
                    f"event:{event_id}",
                    json.dumps(event.dict()),
                    ex=86400  # TTL 24 часа
                )
            except Exception as e:
                print(f"⚠️ Ошибка Redis: {str(e)}")

        return {
            "status": "success",
            "event_id": event_id,
            "message": "Event processed",
            "rabbitmq": app.state.rabbit_ready,
            "redis": app.state.redis_ready
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Проверка статуса сервисов"""
    return {
        "status": "running",
        "rabbitmq": app.state.rabbit_ready,
        "redis": app.state.redis_ready
    }

@app.get("/analytics/events")
async def get_events(
        start_time: datetime = Query(..., description="Start time in ISO format"),
        end_time: datetime = Query(..., description="End time in ISO format"),
        event_name: str = Query(None),
        profile_id: str = Query(None),
        db: AsyncSession = Depends(get_db)
):
    query = select(EventIncomingORM).where(
        EventIncomingORM.event_datetime >= start_time,
        EventIncomingORM.event_datetime <= end_time
    )

    if event_name:
        query = query.where(EventIncomingORM.event_name == event_name)
    if profile_id:
        query = query.where(EventIncomingORM.profile_id == profile_id)

    result = await db.execute(query)
    return result.scalars().all()


@app.get("/analytics/stats")
async def get_stats(
        start_time: datetime = Query(..., description="Start time in ISO format"),
        end_time: datetime = Query(..., description="End time in ISO format"),
        db: AsyncSession = Depends(get_db)
):
    stats_query = (
        select(
            EventIncomingORM.event_name,
            func.count().label("total"),
            func.min(EventIncomingORM.event_datetime).label("first_occurrence"),
            func.max(EventIncomingORM.event_datetime).label("last_occurrence")
        )
        .where(EventIncomingORM.event_datetime.between(start_time, end_time))
        .group_by(EventIncomingORM.event_name)
    )

    result = await db.execute(stats_query)
    return [
        {
            "event_name": row.event_name,
            "total": row.total,
            "first_occurrence": row.first_occurrence,
            "last_occurrence": row.last_occurrence
        }
        for row in result.all()
    ]

# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)



if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",

    )