from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import io
import csv

from ..db import get_db
from ..models import Domain, Score, Feature, Alert, AlertStatus, User
from pydantic import BaseModel
from ..core.celery_app import celery_app
from ..services.ingestion import scheduled_ingestion, fast_scoring_task
from .deps import get_current_active_user

router = APIRouter()

class AnalyzeRequest(BaseModel):
    domain_name: str
    source: Optional[str] = "manual"

@router.post("/domains/analyze", tags=["Domains"])
def analyze_domain_live(request: AnalyzeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Manually input a domain for live tracking."""
    # For MVP, we simulate dropping it into the pipeline directly
    from ..services.ingestion import fetch_crtsh_domains
    
    domain_name = request.domain_name.strip().lower().replace("https://", "").replace("http://", "").split('/')[0]
    
    # Check existing
    domain = db.query(Domain).filter(Domain.domain_name == domain_name).first()
    if not domain:
        from ..models import ProcessingState
        import tldextract
        ext = tldextract.extract(domain_name)
        registered_domain = f"{ext.domain}.{ext.suffix}" if ext.suffix else None
        
        domain = Domain(
            domain_name=domain_name, 
            registered_domain=registered_domain,
            source=request.source, 
            status=ProcessingState.received
        )
        db.add(domain)
        db.commit()
        db.refresh(domain)
        
        celery_app.send_task("app.services.ingestion.fast_scoring_task", args=[domain.id])
    
    return {
        "id": domain.id,
        "domain_name": domain.domain_name,
        "source": domain.source,
        "status": domain.status.value,
        "created_at": domain.created_at,
        "risk_score": 0,
        "top_factors": {}
    }

@router.post("/extension/analyze", tags=["Extension"])
def analyze_domain_extension(request: AnalyzeRequest, x_api_key: str = Header(None), db: Session = Depends(get_db)):
    """Extension endpoint for authenticated domains."""
    if x_api_key != "ext_alpha_dev_key":
        raise HTTPException(status_code=401, detail="Invalid API Key")
        
    from ..services.ingestion import fetch_crtsh_domains
    
    domain_name = request.domain_name.strip().lower().replace("https://", "").replace("http://", "").split('/')[0]
    
    # Check existing
    domain = db.query(Domain).filter(Domain.domain_name == domain_name).first()
    if not domain:
        from ..models import ProcessingState
        import tldextract
        ext = tldextract.extract(domain_name)
        registered_domain = f"{ext.domain}.{ext.suffix}" if ext.suffix else None
        
        domain = Domain(
            domain_name=domain_name, 
            registered_domain=registered_domain,
            source="browser_extension", 
            status=ProcessingState.received
        )
        db.add(domain)
        db.commit()
        db.refresh(domain)
        
        celery_app.send_task("app.services.ingestion.fast_scoring_task", args=[domain.id])
    
    return {"message": "Domain queued for analysis", "domain_id": domain.id}

@router.get("/domains", tags=["Domains"])
def list_domains(status: str = None, limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Get list of domains with optional filtering"""
    from ..models import Alert
    
    query = db.query(Domain, Alert).outerjoin(Alert, Domain.id == Alert.domain_id)
    if status:
        query = query.filter(Domain.status == status)
        
    results = query.order_by(desc(Domain.created_at)).limit(limit).all()
    
    domains_data = []
    for domain, alert in results:
        score_val = 0
        score_record = db.query(Score).filter(Score.domain_id == domain.id).first()
        if score_record:
            score_val = score_record.final_risk_score
            
        domains_data.append({
            "id": domain.id,
            "domain_name": domain.domain_name,
            "source": domain.source,
            "status": domain.status.value,
            "created_at": domain.created_at,
            "risk_score": score_val,
            "alert_id": alert.id if alert else None,
            "alert_status": alert.status.value if alert else None
        })
        
    return domains_data

@router.get("/domains/{domain_id}", tags=["Domains"])
def get_domain_detail(domain_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Fetches details for a specific domain including raw features and enrichment."""
    from ..models import Alert
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
        
    alert = db.query(Alert).filter(Alert.domain_id == domain_id).first()
        
    return {
        "domain": {
            "id": domain.id,
            "domain_name": domain.domain_name,
            "status": domain.status.value,
            "created_at": domain.created_at,
            "alert_id": alert.id if alert else None,
            "alert_status": alert.status.value if alert else None
        },
        "score": {
            "risk_score": domain.score.final_risk_score if domain.score else None,
            "top_factors": domain.score.top_factors if domain.score else None
        },
        "features": {
            "entropy": domain.features.entropy if domain.features else None,
            "length": domain.features.length if domain.features else None,
            "digit_ratio": domain.features.digit_ratio if domain.features else None,
            "keyword_match": domain.features.keyword_match if domain.features else None,
            "levenshtein_min": domain.features.levenshtein_min if domain.features else None
        } if domain.features else {},
        "enrichment": {
            "rdap_registrar": domain.enrichment.rdap_registrar if domain.enrichment else None,
            "dns_a_record_count": domain.enrichment.dns_a_record_count if domain.enrichment else 0,
            "cert_issuer": domain.enrichment.cert_issuer if domain.enrichment else None
        } if domain.enrichment else {}
    }

class ReviewRequest(BaseModel):
    status: AlertStatus
    notes: Optional[str] = None

@router.post("/alerts/{alert_id}/review", tags=["Analyst Workflow"])
def review_alert(alert_id: int, request: ReviewRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Analyst workflow to confirm or dismiss an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert.status = request.status
    alert.notes = request.notes
    alert.analyst_id = current_user.id
    db.commit()
    return {"message": "Alert updated successfully"}

@router.get("/export/domains", tags=["Export"])
def export_domains(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Exports all domains to CSV."""
    domains = db.query(Domain).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Domain", "Status", "Source", "Created At"])
    
    for d in domains:
        writer.writerow([d.id, d.domain_name, d.status.value, d.source, d.created_at])
        
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=domains_export.csv"})
