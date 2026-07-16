import httpx
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def get_rdap_data(domain: str) -> dict:
    """
    Fetches structured RDAP registration data for a domain.
    """
    # Use a public RDAP bootstrap or a specific RDAP server
    url = f"https://rdap.org/domain/{domain}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant fields
                events = data.get("events", [])
                reg_date = None
                exp_date = None
                for event in events:
                    if event.get("eventAction") == "registration":
                        reg_date = event.get("eventDate")
                    elif event.get("eventAction") == "expiration":
                        exp_date = event.get("eventDate")
                        
                # Registrar
                entities = data.get("entities", [])
                registrar = None
                for entity in entities:
                    if "registrar" in entity.get("roles", []):
                        vcard = entity.get("vcardArray", [])
                        if len(vcard) > 1:
                            for prop in vcard[1]:
                                if prop[0] == "fn":
                                    registrar = prop[3]
                                    break
                
                # Calculate age and parse dates
                age_days = None
                reg_dt = None
                exp_dt = None
                if reg_date:
                    try:
                        # RDAP dates are usually ISO8601
                        reg_dt = datetime.fromisoformat(reg_date.replace("Z", "+00:00"))
                        age_days = (datetime.now(reg_dt.tzinfo) - reg_dt).days
                    except Exception:
                        pass
                if exp_date:
                    try:
                        exp_dt = datetime.fromisoformat(exp_date.replace("Z", "+00:00"))
                    except Exception:
                        pass
                        
                return {
                    "rdap_registration_date": reg_dt,
                    "rdap_expiry_date": exp_dt,
                    "rdap_registrar": registrar,
                    "rdap_domain_age_days": age_days,
                    "status": "success"
                }
    except Exception as e:
        logger.error(f"RDAP lookup failed for {domain}: {e}")
        
    return {
        "status": "failed"
    }
