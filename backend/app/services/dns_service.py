"""
DNS Service

This module provides functionalities for fetching DNS records (A, MX, NS) for a given domain.
"""

import asyncio
import logging
import socket
from typing import Any, Dict, List

# Configure logger for this module
logger = logging.getLogger(__name__)


async def get_dns_data(domain: str) -> Dict[str, Any]:
    """
    Asynchronously fetches DNS records for a given domain.
    
    Currently implemented:
        - A Records (IPv4 addresses)
        
    Placeholders for future implementation:
        - MX Records (Mail Exchange)
        - NS Records (Name Servers)
        
    Args:
        domain (str): The domain name to query (e.g., 'example.com').
        
    Returns:
        Dict[str, Any]: A dictionary containing the DNS record counts and lookup status.
    """
    
    # Initialize the default response structure
    dns_results: Dict[str, Any] = {
        "dns_a_record_count": 0,
        "dns_mx_record_present": False,
        "dns_ns_record_count": 0,
        "status": "success",
    }
    
    try:
        # Fetch A records using the standard socket library running in an executor
        # to prevent blocking the async event loop
        a_records = await _fetch_a_records(domain)
        dns_results["dns_a_record_count"] = len(a_records)
        
        # TODO: Implement MX and NS record lookups asynchronously.
        # Note: Standard socket library has limitations for async MX/NS queries.
        # Recommendation: Use a third-party library like `aiodns` for production.
        
    except Exception as error:
        # Log unexpected errors and mark the status as failed
        logger.error(f"DNS lookup failed for domain '{domain}': {error}")
        dns_results["status"] = "failed"
        
    return dns_results


async def _fetch_a_records(domain: str) -> List[str]:
    """
    Helper function to fetch A records for a domain.
    
    Args:
        domain (str): The domain name.
        
    Returns:
        List[str]: A list of IP addresses associated with the domain.
    """
    loop = asyncio.get_running_loop()
    try:
        # socket.gethostbyname_ex returns a tuple: (hostname, aliaslist, ipaddrlist)
        _, _, ip_addresses = await loop.run_in_executor(
            None, socket.gethostbyname_ex, domain
        )
        return ip_addresses
    except socket.gaierror:
        # Expected exception if the domain has no A records or doesn't exist
        return []
