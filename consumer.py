import asyncio
import json
from datetime import datetime
from ctypes import cdll, c_char_p
from aioredis import Redis
import aio_pika
from src.config import settings
from src.database import get_db
from src.ORM_models import EventIncomingORM

# Инициализация Go-библиотеки
lib = cdll.LoadLibrary('./libdedup.so')
lib.GenerateEventHash.argtypes = [c_char_p]
lib.GenerateEventHash.restype = c_char_p


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        redis = None
        try:
            data = json.loads(message.body.decode())

            # Генерация хеша
            json_str = json.dumps(data).encode()
            hash_str = lib.GenerateEventHash(json_str).decode()

            # Подключение к Redis
            redis = Redis.from_url(settings.REDIS_URL)

            if await redis.exists(hash_str):
                await message.reject(requeue=False)
                return

            await redis.setex(hash_str, 7 * 86400, 1)

            # Сохранение в PostgreSQL
            async with get_db() as session:
                event = EventIncomingORM(
                    event_hash=hash_str,
                    event_name=data.get('event_name'),
                    event_datetime=datetime.fromisoformat(data['event_datetime']),
                    profile_id=data.get('profile_id'),
                    device_ip=data.get('device_ip'),
                    raw_data=data
                )
                session.add(event)
                await session.commit()

            await message.ack()
        except Exception as e:
            await message.reject(requeue=False)
            print(f"Error: {str(e)}")
        finally:
            if redis:
                await redis.close()


async def main():
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        queue = await channel.declare_queue(
            "events",
            durable=True,
            arguments={"x-queue-type": "quorum"}
        )

        await queue.consume(process_message)
        print("Consumer started. Waiting for messages...")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
