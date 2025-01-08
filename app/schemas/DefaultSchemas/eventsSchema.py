from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from schemas.DefaultSchemas.tasksSchema import Task

class EventBase(BaseModel):
    name: str
    desc: str
    date: datetime
    

class EventCreate(EventBase):
    id: int


class Event(EventBase):
    id: int
    tasks: List[Optional[Task]]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
