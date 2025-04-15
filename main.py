import os
import json
from contextlib import asynccontextmanager
from datetime import datetime
import aio_pika
import uvicorn
from fastapi import FastAPI, Query, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.ORM_models import EventIncomingORM
from src.database import get_db

from src.models import EventRequest, EventCreateSchema
from src.repository import EventRepository
from utils.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
    # Устанавливаем соединение с RabbitMQ
    connection = await aio_pika.connect_robust(
        rabbitmq_url,
        timeout=30
    )
    # Сохраняем соединение и канал напрямую в app.state
    app.state.rabbit_connection = connection
    app.state.rabbit_channel = await connection.channel()
    yield
    # Корректное закрытие соединения при завершении
    await connection.close()
app = FastAPI(lifespan=lifespan)

# !!! Делаем всё явно, Задалбало
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME = "events"


async def get_rabbit_channel():
    """Создает и возвращает канал RabbitMQ"""
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    # Объявляем очередь с durability
    await channel.declare_queue(QUEUE_NAME, durable=True)
    return channel


@app.post("/events")
async def create_event(
        event: EventCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    try:
        # !!! 1. Сохраняем событие в БД
        event_id = await EventRepository.add_event(event, db)

        # !!! 2. Отправляем событие в RabbitMQ
        try:
            channel = await get_rabbit_channel()
            message_body = json.dumps(event.model_dump()).encode()

            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=QUEUE_NAME
            )

            await channel.close()
        except Exception as e:
            # Логируем, но не прерываем
            print(f"RabbitMQ error: {str(e)}")

        return {
            "status": "success",
            "event_id": event_id,
            "message": "Event stored and queued"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Ручное тестирование беp RabbitMQ
# @app.post("/events")
# async def create_event(
#     event: EventCreateSchema,
#     db: AsyncSession = Depends(get_db)
# ):
#     try:
#         # Без RabbitMQ
#         event_id = await EventRepository.add_event(event, db)
#         return {"status": "success", "event_id": event_id}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
