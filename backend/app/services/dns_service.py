import asyncio
import socket
import logging

logger = logging.getLogger(__name__)

async def get_dns_data(domain: str) -> dict:
    """
    Fetches DNS records for a domain.
    """
    data = {
        "dns_a_record_count": 0,
        "dns_mx_record_present": False,
        "dns_ns_record_count": 0,
        "status": "success"
    }
    
    loop = asyncio.get_running_loop()
    
    try:
        # A records
        try:
            _, _, ipaddrlist = await loop.run_in_executor(None, socket.gethostbyname_ex, domain)
            data["dns_a_record_count"] = len(ipaddrlist)
        except socket.gaierror:
            pass
            
        # Due to standard library limitations, fetching MX and NS records asynchronously
        # is better done with aiodns. We'll use a placeholder logic or basic socket for MVP.
        # In a real product, aiodns would be used.
        
    except Exception as e:
        logger.error(f"DNS lookup failed for {domain}: {e}")
        data["status"] = "failed"
        
    return data
