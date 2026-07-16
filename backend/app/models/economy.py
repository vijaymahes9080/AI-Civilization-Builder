import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from backend.app.database import Base

class MarketModel(Base):
    __tablename__ = "markets"
    
    id = Column(String(36), primary_key=True, index=True)
    world_id = Column(String(36), ForeignKey("worlds.id"), nullable=False)
    name = Column(String(255), nullable=False)
    pos_x = Column(Integer, default=0)
    pos_y = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class TransactionModel(Base):
    __tablename__ = "transactions"
    
    id = Column(String(36), primary_key=True, index=True)
    world_id = Column(String(36), ForeignKey("worlds.id"), nullable=False)
    market_id = Column(String(36), ForeignKey("markets.id"), nullable=False)
    buyer_id = Column(String(36), nullable=True)  # Can be empty for public supply
    seller_id = Column(String(36), nullable=True) # Can be empty for public purchases
    resource_type = Column(String(50), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    tick = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
