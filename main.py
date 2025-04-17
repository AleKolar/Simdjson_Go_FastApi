from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from redis_client import get_redis
from src.ORM_models import EventIncomingORM
from src.database import get_db
from src.models import EventCreateSchema
from src.repository import EventRepository

# Простая реализация без всего для проверки сборки
app = FastAPI()

@app.post("/api/events", status_code=status.HTTP_201_CREATED)
async def process_event(
    event: EventIncomingORM,  
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """Обработка входящего события через API"""
    try:
        event_db = EventCreateSchema(
            event_name=event.event_name,
            event_datetime=event.event_datetime,
            profile_id=event.profile_id,  
            device_ip=event.device_ip,
            raw_data=event.raw_data
        )
        
        db_event = await EventRepository.create_event(event_db, db, redis)

        if not db_event:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Обнаружено дублирующееся событие"
            )

        return {
            "status": "processed",
            "event_id": db_event.event_hash,
            "details": db_event.model_dump()
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обработки: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)




if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",

    )
