import json
from datetime import datetime, timezone
from ctypes import cdll, c_char_p
from aioredis import Redis
import aio_pika
from sqlalchemy import insert
from .models import Event
from .database import get_db

lib = cdll.LoadLibrary('./libdedup.so')
lib.GenerateEventHash.argtypes = [c_char_p]
lib.GenerateEventHash.restype = c_char_p


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())

        # Генерация хеша
        json_str = json.dumps(data).encode()
        hash_str = lib.GenerateEventHash(json_str).decode()

        # Проверка дубликата
        redis = await Redis.from_url("redis://redis:6379")
        if await redis.exists(hash_str):
            return

        # Сохранение в Redis
        await redis.setex(hash_str, 7 * 86400, 1)

        # Извлечение ключевых полей
        event_name = data.get('event_name')
        event_datetime = datetime.fromisoformat(data.get('event_datetime_str'))
        profile_id = data.get('profile_id') or data.get('device_ip')

        # Сохранение в PostgreSQL
        async with get_db() as session:
            stmt = insert(Event).values(
                event_hash=hash_str,
                event_name=event_name,
                event_datetime=event_datetime,
                profile_id=profile_id,
                device_ip=data.get('device_ip'),
                raw_data=data,
                created_at=datetime.datetime.now(timezone.utc).isoformat()
            )
            await session.execute(stmt)
            await session.commit()
