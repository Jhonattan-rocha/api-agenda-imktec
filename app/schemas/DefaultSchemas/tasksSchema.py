from pydantic import BaseModel

class TaskBase(BaseModel):
    name: str
    desc: str
    date: str
    ready: bool
    event_id: int
    

class TaskCreate(TaskBase):
    id: int


class Task(TaskBase):
    id: int

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
