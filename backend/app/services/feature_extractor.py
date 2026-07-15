import math
import Levenshtein

# Mock list of targeted brands
KNOWN_BRANDS = ["paypal", "apple", "microsoft", "google", "amazon", "netflix", "facebook"]

def calculate_entropy(text: str) -> float:
    if not text:
        return 0.0
    entropy = 0
    for x in set(text):
        p_x = float(text.count(x)) / len(text)
        entropy += - p_x * math.log2(p_x)
    return entropy

def extract_lexical_features(domain: str) -> dict:
    """Extracts lexical features from a domain string."""
    # Remove TLD for some checks
    parts = domain.split('.')
    base_name = parts[0] if parts else domain
    
    length = len(domain)
    entropy = calculate_entropy(base_name)
    
    digit_count = sum(c.isdigit() for c in base_name)
    digit_ratio = digit_count / len(base_name) if len(base_name) > 0 else 0
    
    hyphen_count = base_name.count('-')
    
    keyword_match = any(brand in base_name.lower() for brand in KNOWN_BRANDS)
    
    # Calculate min Levenshtein distance to known brands
    lev_min = min((Levenshtein.distance(base_name.lower(), brand) for brand in KNOWN_BRANDS), default=0)

    return {
        "length": length,
        "entropy": round(entropy, 3),
        "digit_ratio": round(digit_ratio, 3),
        "hyphen_count": hyphen_count,
        "keyword_match": keyword_match,
        "levenshtein_min": lev_min
    }
