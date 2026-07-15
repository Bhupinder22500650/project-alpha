import asyncio
import httpx
from sqlalchemy.orm import Session
import logging
from ..db import SessionLocal
from ..models import Domain, Feature, Score
from .scorer import score_domain
from .whois_service import get_whois_data

logger = logging.getLogger(__name__)

async def fetch_crtsh_domains():
    """Fetches recent domain registrations from crt.sh (Certificate Transparency logs)."""
    # For MVP, we query for a common keyword or just a recent generic block.
    # crt.sh can be slow, so we timeout quickly.
    url = "https://crt.sh/?q=paypal&output=json" 
    # Using a targeted query to simulate finding brand impersonations for the prototype demo.
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                # Deduplicate domains, limit to top 50 for prototype speed
                domains = list(set([entry['name_value'].lower() for entry in data]))[:50]
                # clean wildcards
                domains = [d.replace('*.', '') for d in domains]
                return list(set(domains))
    except Exception as e:
        logger.error(f"Failed to fetch from crt.sh: {e}")
    
    return []

def process_new_domains():
    """Main ingestion job: fetch, score, and store."""
    logger.info("Starting domain ingestion job...")
    
    # We must run the async fetch in a synchronous wrapper for APScheduler easily
    domains = asyncio.run(fetch_crtsh_domains())
    
    if not domains:
        logger.info("No domains fetched.")
        return

    db: Session = SessionLocal()
    
    new_count = 0
    for domain_name in domains:
        # Check if exists
        existing = db.query(Domain).filter(Domain.domain_name == domain_name).first()
        if existing:
            continue
            
        new_count += 1
        
        # 1. Create Domain
        db_domain = Domain(domain_name=domain_name, source="crt.sh", status="pending")
        db.add(db_domain)
        db.commit()
        db.refresh(db_domain)
        
        # 2. Extract Features & WHOIS
        # whois_data = get_whois_data(domain_name) # Skipped for MVP speed, but available
        score_result = score_domain(domain_name)
        feats = score_result['features']
        
        db_feature = Feature(
            domain_id=db_domain.id,
            length=feats['length'],
            entropy=feats['entropy'],
            digit_ratio=feats['digit_ratio'],
            hyphen_count=feats['hyphen_count'],
            keyword_match=feats['keyword_match'],
            levenshtein_min=feats['levenshtein_min']
        )
        db.add(db_feature)
        
        # 3. Save Score
        db_score = Score(
            domain_id=db_domain.id,
            risk_score=score_result['risk_score'],
            top_factors=score_result['top_factors']
        )
        db.add(db_score)
        
        # 4. Update status
        db_domain.status = "scored"
        db.commit()
        
    logger.info(f"Ingestion complete. Processed {new_count} new domains.")
    db.close()
