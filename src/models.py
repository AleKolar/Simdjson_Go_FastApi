from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

class RawDataSchema(BaseModel):
    content_type: str = ""
    content_gid: str = ""
    content_name: str = ""
    content_id: str = ""
    promocode: str = ""
    promocode_code: str = ""
    quality: str = ""
    play_url: str = ""
    channel_name: str = ""
    channel_id: str = ""
    channel_gid: str = ""
    cause: str = ""
    button_id: str = ""
    button_text: str = ""
    feedback_text: str = ""
    experiments: List[str] = []
    season: str = ""
    episode: str = ""

class EventRequest(BaseModel):
    event_name: str
    event_datetime: datetime
    profile_id: str
    device_ip: str
    raw_data: Dict[str, Any]

class EventCreateSchema(EventRequest):
    raw_data: RawDataSchema
    model_config = ConfigDict(from_attributes=True)
