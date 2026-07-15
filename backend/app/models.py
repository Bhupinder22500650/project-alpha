from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from .db import Base

class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True)
    domain_name = Column(String, unique=True, index=True, nullable=False)
    source = Column(String, default="crt.sh")
    status = Column(String, default="pending") # pending, scored, alerted
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, index=True)
    length = Column(Integer)
    entropy = Column(Float)
    digit_ratio = Column(Float)
    hyphen_count = Column(Integer)
    keyword_match = Column(Boolean, default=False)
    levenshtein_min = Column(Integer)
    extracted_at = Column(DateTime(timezone=True), server_default=func.now())

class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, index=True)
    risk_score = Column(Float, nullable=False) # 0 to 100
    model_version = Column(String, default="v1.0")
    top_factors = Column(JSON) # e.g. {"entropy": 0.3, "length": 0.2}
    scored_at = Column(DateTime(timezone=True), server_default=func.now())
