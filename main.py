import os
import sys
from datetime import datetime
import uvicorn
from fastapi import FastAPI, Query, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from src.models import Event

app = FastAPI()


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
