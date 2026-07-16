import datetime
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ForeignKey
from backend.app.database import Base

class GovernmentModel(Base):
    __tablename__ = "governments"
    
    id = Column(String(36), primary_key=True, index=True)
    world_id = Column(String(36), ForeignKey("worlds.id"), nullable=False)
    regime_type = Column(String(50), default="DEMOCRACY")  # DEMOCRACY, REPUBLIC, MONARCHY, ANARCHY
    tax_rate = Column(Float, default=0.1)
    social_welfare_rate = Column(Float, default=0.0)
    stability = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class LawModel(Base):
    __tablename__ = "laws"
    
    id = Column(String(36), primary_key=True, index=True)
    government_id = Column(String(36), ForeignKey("governments.id"), nullable=False)
    title = Column(String(255), nullable=False)
    code_expression = Column(String(1024), nullable=False)  # Custom Python executable logic (e.g. tax calculations, zoning constraints)
    enforced_status = Column(Boolean, default=True)
    passed_tick = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
