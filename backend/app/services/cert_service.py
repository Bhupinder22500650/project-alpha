import ssl
import socket
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def get_cert_data(domain: str) -> dict:
    """
    Fetches SSL certificate metadata for a domain.
    """
    data = {
        "cert_issuer": None,
        "cert_validity_days": None,
        "status": "success"
    }
    
    loop = asyncio.get_running_loop()
    
    def fetch_cert():
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=3.0) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                return ssock.getpeercert()
                
    try:
        cert = await loop.run_in_executor(None, fetch_cert)
        
        # Extract issuer
        issuer = dict(x[0] for x in cert.get("issuer", []))
        data["cert_issuer"] = issuer.get("organizationName", issuer.get("commonName"))
        
        # Extract validity
        not_before = datetime.strptime(cert["notBefore"], "%b %d %H:%M:%S %Y %Z")
        not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        data["cert_validity_days"] = (not_after - not_before).days
        
    except Exception as e:
        logger.error(f"Cert lookup failed for {domain}: {e}")
        data["status"] = "failed"
        
    return data
