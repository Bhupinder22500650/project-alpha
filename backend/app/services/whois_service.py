import whois
import redis
from ..core.config import settings
import json
import logging

logger = logging.getLogger(__name__)

# Attempt to connect to Redis, but gracefully fail if not available during dev
try:
    cache = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
except Exception:
    cache = None

CACHE_TTL = 86400 # 24 hours

def get_whois_data(domain: str) -> dict:
    """Fetches WHOIS data, utilizing Redis cache to prevent rate limits."""
    cache_key = f"whois:{domain}"
    
    if cache:
        try:
            cached = cache.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Redis cache error: {e}")

    try:
        w = whois.whois(domain)
        data = {
            "registrar": w.registrar if isinstance(w.registrar, str) else "Unknown",
            "creation_date": str(w.creation_date[0]) if isinstance(w.creation_date, list) else str(w.creation_date),
            "country": w.country if isinstance(w.country, str) else "Unknown"
        }
    except Exception as e:
        logger.error(f"WHOIS lookup failed for {domain}: {e}")
        data = {"registrar": "Error", "creation_date": "Error", "country": "Error"}

    if cache and data["registrar"] != "Error":
        try:
            cache.setex(cache_key, CACHE_TTL, json.dumps(data))
        except Exception:
            pass

    return data
