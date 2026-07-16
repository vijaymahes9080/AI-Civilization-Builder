import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from backend.app.database import Base

class CitizenModel(Base):
    __tablename__ = "citizens"
    
    id = Column(String(36), primary_key=True, index=True)
    world_id = Column(String(36), ForeignKey("worlds.id"), nullable=False)
    name = Column(String(255), nullable=False)
    age = Column(Float, default=0.0)
    health = Column(Float, default=100.0)
    wealth = Column(Float, default=10.0)
    occupation = Column(String(255), nullable=True)
    
    # Grid Coordinates
    pos_x = Column(Integer, default=0)
    pos_y = Column(Integer, default=0)
    
    # Big Five Personality Traits (0.0 to 1.0)
    personality_o = Column(Float, default=0.5)  # Openness
    personality_c = Column(Float, default=0.5)  # Conscientiousness
    personality_e = Column(Float, default=0.5)  # Extraversion
    personality_a = Column(Float, default=0.5)  # Agreeableness
    personality_n = Column(Float, default=0.5)  # Neuroticism
    
    # Genetic DNA sequence representation
    dna_sequence = Column(String(512), nullable=True)
    
    # Social/Relationship metrics
    trust_score = Column(Float, default=0.5)
    reputation = Column(Float, default=0.5)
    
    # Family Tree Connections
    parent1_id = Column(String(36), nullable=True)
    parent2_id = Column(String(36), nullable=True)
    spouse_id = Column(String(36), nullable=True)
    
    # Lifecycle flags
    is_alive = Column(Boolean, default=True)
    cause_of_death = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
