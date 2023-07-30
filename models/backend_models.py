import datetime
from typing import Optional

from pydantic import BaseModel

import settings


class Video(BaseModel):
    id: int
    name: str
    finish_record: Optional[datetime.datetime] =  None

    def to_json(self):
        return self.model_dump_json()


class Telemetry(BaseModel):
    id: int
    zone: int
    polygon: int
    time: datetime.datetime
    video_time: datetime.time

    def to_json(self):
        return self.model_dump_json()


class TelemetryButch(BaseModel):
    event_id: int
    video_data: Video
    events_data: list[Telemetry]
    area_id: int = settings.AREA_ID

    def to_json(self):
        return self.model_dump_json()
