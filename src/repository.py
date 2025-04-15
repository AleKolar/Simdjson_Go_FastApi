from datetime import datetime
from sqlalchemy import select

from src.ORM_models import EventORM
from src.database import new_session
from src.models import EventRequest


class EventRepository:
    @classmethod
    async def add_event(cls, event_request: EventRequest) -> int:
        async with new_session() as session:
            data = event_request.model_dump()  # Конвертация в словарь
            new_event = EventORM(**data)  # Создание ORM объекта
            session.add(new_event)  # Добавление нового события
            await session.flush()  # Обновление объекта
            await session.commit()  # Коммит транзакции
            return new_event.id  # Возврат ID нового события

    @classmethod
    async def get_events(cls) -> list[EventRequest]:
        async with new_session() as session:
            query = select(EventORM)  # Запрос для получения всех событий
            result = await session.execute(query)  # Выполнение запроса
            event_models = result.scalars().all()  # Получение всех результатов
            events = [EventRequest(**event_model.model_dump()) for event_model in
                      event_models]  # Конвертация в Pydantic
            return events  # Возврат списка событий


# Пример использования
async def main():
    # Пример добавления события
    new_event = EventRequest(
        platform="web",
        event_name="page_view",
        event_datetime=datetime.now(),
        profile_id="user_123",
        device_ip="192.168.1.1",
        raw_data={"details": "some details"},
        created_at=datetime.now(),
    )

    event_id = await EventRepository.add_event(new_event)
    print(f"Added event with ID: {event_id}")

    # Пример получения всех событий
    events = await EventRepository.get_events()
    for event in events:
        print(event)

    # Используйте asyncio для запуска main


import asyncio

asyncio.run(main())