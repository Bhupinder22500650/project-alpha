from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from ..db import get_db
from ..models import Domain, Score, Feature

router = APIRouter()

@router.get("/domains", tags=["Domains"])
def get_domains(limit: int = 50, skip: int = 0, min_risk: float = 0, db: Session = Depends(get_db)):
    """Fetches latest scored domains."""
    query = db.query(Domain, Score).join(Score, Domain.id == Score.domain_id)\
              .filter(Score.risk_score >= min_risk)\
              .order_by(desc(Score.risk_score), desc(Domain.created_at))
              
    results = query.offset(skip).limit(limit).all()
    
    response = []
    for domain, score in results:
        response.append({
            "id": domain.id,
            "domain_name": domain.domain_name,
            "source": domain.source,
            "status": domain.status,
            "created_at": domain.created_at,
            "risk_score": score.risk_score,
            "top_factors": score.top_factors
        })
    return response

@router.get("/domains/{domain_id}", tags=["Domains"])
def get_domain_detail(domain_id: int, db: Session = Depends(get_db)):
    """Fetches details for a specific domain including raw features."""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
        
    score = db.query(Score).filter(Score.domain_id == domain_id).first()
    features = db.query(Feature).filter(Feature.domain_id == domain_id).first()
    
    return {
        "domain": {
            "id": domain.id,
            "domain_name": domain.domain_name,
            "created_at": domain.created_at
        },
        "score": {
            "risk_score": score.risk_score if score else None,
            "top_factors": score.top_factors if score else None
        },
        "features": {
            "entropy": features.entropy if features else None,
            "length": features.length if features else None,
            "digit_ratio": features.digit_ratio if features else None,
            "keyword_match": features.keyword_match if features else None,
            "levenshtein_min": features.levenshtein_min if features else None
        }
    }
