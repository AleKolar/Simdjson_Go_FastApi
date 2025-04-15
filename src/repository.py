from sqlalchemy import select
from src.models import EventRequest


from sqlalchemy.ext.asyncio import AsyncSession
from .ORM_models import EventIncomingORM
from .models import EventCreateSchema

class EventRepository:
    @staticmethod
    async def add_event(event_data: EventCreateSchema, db: AsyncSession) -> int:
        try:
            db_event = EventIncomingORM(**event_data.model_dump())
            db.add(db_event)
            await db.commit()
            await db.refresh(db_event)
            return db_event.id
        except Exception as e:
            await db.rollback()
            raise

    @classmethod
    async def get_events(cls, db: AsyncSession) -> list[EventRequest]:
        result = await db.execute(select(EventIncomingORM))
        return [
            EventRequest.model_validate(event.__dict__)
            for event in result.scalars().all()
        ]


# Пример использования получения всех событий
# async def main():
#     # Пример добавления события
#     new_event = EventRequest(
#         platform="web",
#         event_name="page_view",
#         event_datetime=datetime.now(),
#         profile_id="user_123",
#         device_ip="192.168.1.1",
#         raw_data={"details": "some details"},
#         created_at=datetime.now(),
#     )
#
#     event_id = await EventRepository.add_event(new_event)
#     print(f"Added event with ID: {event_id}")

    # Для получения всех событий (пример)
#     events = await EventRepository.get_events()
#     for event in events:
#         print(event)
#
#
#
# import asyncio
#
# asyncio.run(main())