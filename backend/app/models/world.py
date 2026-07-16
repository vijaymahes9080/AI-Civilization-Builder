import datetime
from sqlalchemy import Column, String, Integer, DateTime
from backend.app.database import Base

class WorldModel(Base):
    __tablename__ = "worlds"
    
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    seed = Column(Integer, nullable=False)
    current_tick = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
