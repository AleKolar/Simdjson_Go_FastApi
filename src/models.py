from sqlalchemy import Column, String, DateTime, JSON, Integer, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    event_hash = Column(String(64), unique=True, nullable=False)
    event_name = Column(String(100), index=True)  # Для фильтрации по имени
    event_datetime = Column(DateTime, index=True)  # Для временных диапазонов
    profile_id = Column(String(50), index=True)  # Основной идентификатор
    device_ip = Column(String(15))  # Доп. идентификатор
    raw_data = Column(JSON)  # Все исходные данные
    created_at = Column(DateTime)  # Время обработки


Index("idx_main_analytics", "event_name", "event_datetime", "profile_id")