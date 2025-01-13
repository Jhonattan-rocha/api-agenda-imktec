from sqlalchemy import Column, Integer, Boolean, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship


class Notification(Base):
    __tablename__ = "notifi"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    send = Column(Boolean, default=False)
    view = Column(Boolean, default=False)
    
    user = relationship("User", lazy="joined")
    event = relationship("Events", lazy="joined")
    task = relationship("Tasks", lazy="joined")
