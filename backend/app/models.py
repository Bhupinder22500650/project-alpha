from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .db import Base

class UserRole(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.analyst)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProcessingState(str, enum.Enum):
    received = "received"
    normalised = "normalised"
    initially_scored = "initially_scored"
    enrichment_pending = "enrichment_pending"
    enriching = "enriching"
    fully_scored = "fully_scored"
    enrichment_failed = "enrichment_failed"
    reviewed = "reviewed"
    closed = "closed"

class Domain(Base):
    __tablename__ = "domains"
    id = Column(Integer, primary_key=True, index=True)
    domain_name = Column(String, unique=True, index=True, nullable=False)
    registered_domain = Column(String, index=True, nullable=True)
    source = Column(String, default="crt.sh")
    status = Column(Enum(ProcessingState), default=ProcessingState.received)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    features = relationship("Feature", back_populates="domain", uselist=False, cascade="all, delete-orphan")
    score = relationship("Score", back_populates="domain", uselist=False, cascade="all, delete-orphan")
    enrichment = relationship("DomainEnrichment", back_populates="domain", uselist=False, cascade="all, delete-orphan")
    alert = relationship("Alert", back_populates="domain", uselist=False, cascade="all, delete-orphan")

class Feature(Base):
    __tablename__ = "features"
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), index=True)
    
    # Fast lexical features
    length = Column(Integer)
    entropy = Column(Float)
    digit_ratio = Column(Float)
    hyphen_count = Column(Integer)
    keyword_match = Column(Boolean, default=False)
    levenshtein_min = Column(Integer)
    extracted_at = Column(DateTime(timezone=True), server_default=func.now())

    domain = relationship("Domain", back_populates="features")

class DomainEnrichment(Base):
    __tablename__ = "domain_enrichments"
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), index=True)
    
    # RDAP
    rdap_registration_date = Column(DateTime(timezone=True), nullable=True)
    rdap_expiry_date = Column(DateTime(timezone=True), nullable=True)
    rdap_registrar = Column(String, nullable=True)
    rdap_domain_age_days = Column(Integer, nullable=True)
    
    # DNS
    dns_a_record_count = Column(Integer, default=0)
    dns_mx_record_present = Column(Boolean, default=False)
    dns_ns_record_count = Column(Integer, default=0)
    
    # Certificate
    cert_issuer = Column(String, nullable=True)
    cert_validity_days = Column(Integer, nullable=True)
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    domain = relationship("Domain", back_populates="enrichment")

class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), index=True)
    
    # Stage 1 Score
    fast_lexical_score = Column(Float, nullable=True)
    
    # Stage 2 Score (Enriched)
    final_risk_score = Column(Float, nullable=False) # 0 to 100
    model_version = Column(String, default="v2.0")
    
    # SHAP explanations
    top_factors = Column(JSON) 
    
    scored_at = Column(DateTime(timezone=True), server_default=func.now())
    
    domain = relationship("Domain", back_populates="score")

class AlertStatus(str, enum.Enum):
    new = "new"
    under_review = "under_review"
    confirmed_suspicious = "confirmed_suspicious"
    false_positive = "false_positive"
    closed = "closed"

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), index=True)
    risk_score = Column(Float, nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.new)
    analyst_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    domain = relationship("Domain", back_populates="alert")
    analyst = relationship("User")
