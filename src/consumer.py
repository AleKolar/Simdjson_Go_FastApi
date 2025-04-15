import os
import json
import asyncio
from datetime import datetime, timezone
from ctypes import cdll, c_char_p
from aioredis import Redis
import aio_pika
from sqlalchemy import insert
from dotenv import load_dotenv

from src.ORM_models import EventORM
from src.database import get_db

load_dotenv()

# Инициализация Go-библиотеки
lib = cdll.LoadLibrary('./libdedup.so')
lib.GenerateEventHash.argtypes = [c_char_p]
lib.GenerateEventHash.restype = c_char_p


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            data = json.loads(message.body.decode())

            # Генерация хеша
            json_str = json.dumps(data).encode()
            hash_str = lib.GenerateEventHash(json_str).decode()

            # Подключение к Redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            redis = Redis.from_url(redis_url)

            # Проверка дубликата
            if await redis.exists(hash_str):
                await message.reject(requeue=False)
                return

            # Сохранение в Redis
            await redis.setex(hash_str, 7 * 86400, 1)

            # Извлечение данных
            event_name = data.get('event_name')
            event_datetime = datetime.fromisoformat(data.get('event_datetime_str'))
            profile_id = data.get('profile_id') or data.get('device_ip')

            # Сохранение в PostgreSQL
            async with get_db() as session:
                stmt = insert(EventORM).values(
                    event_hash=hash_str,
                    event_name=event_name,
                    event_datetime=event_datetime,
                    profile_id=profile_id,
                    device_ip=data.get('device_ip'),
                    raw_data=data,
                    created_at=datetime.now(timezone.utc)
                )
                await session.execute(stmt)
                await session.commit()

            await message.ack()
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            await message.reject(requeue=False)
        except Exception as e:
            print(f"Processing error: {e}")
            await message.reject(requeue=True)
        finally:
            await redis.close()


async def consume_rabbitmq():
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
    connection = await aio_pika.connect_robust(rabbitmq_url)

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        queue = await channel.declare_queue(
            "events",
            durable=True,
            arguments={
                "x-queue-type": "quorum"
            }
        )

        await queue.consume(process_message)
        print("Consumer started. Waiting for messages...")
        await asyncio.Future()  # Бесконечное ожидание


if __name__ == "__main__":
    asyncio.run(consume_rabbitmq())