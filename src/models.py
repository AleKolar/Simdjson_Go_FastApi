import json
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, String, DateTime, JSON, Integer, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class EventIncoming(Base):
    __tablename__ = "events"

    id: [int]
    event_hash: [int]
    event_name: [str] = Index
    event_datetime = []
    profile_id: [int]
    device_ip: [int] = Index
    raw_data: [json]
    created_at: [DateTime]

class SchemaEventIncoming(EventIncoming):
    model_config = ConfigDict(from_attributes=True)


# Схема для событий
class EventRequest(BaseModel):
    platform: Optional[str] = None
    event_name: Optional[str] = None
    event_datetime: Optional[datetime] = None
    profile_id: Optional[str] = None
    device_ip: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Схема для извлечения данных
class SchemaEventRequest(EventIncoming):
    model_config = ConfigDict(from_attributes=True)