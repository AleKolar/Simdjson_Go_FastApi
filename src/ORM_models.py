from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Integer, String, DateTime, JSON, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Model(DeclarativeBase):
    pass


class EventIncomingORM(Model):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    event_name: Mapped[str] = mapped_column(String(100), index=True)
    event_datetime: Mapped[datetime] = mapped_column(DateTime, index=True)
    profile_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    device_ip: Mapped[Optional[str]] = mapped_column(String(15))
    raw_data: Mapped[Dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_main_analytics", "event_name", "event_datetime", "profile_id"),
    )

    def model_dump(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_hash": self.event_hash,
            "event_name": self.event_name,
            "event_datetime": self.event_datetime.isoformat(),
            "profile_id": self.profile_id,
            "device_ip": self.device_ip,
            "raw_data": self.raw_data,
            "created_at": self.created_at.isoformat(),
        }