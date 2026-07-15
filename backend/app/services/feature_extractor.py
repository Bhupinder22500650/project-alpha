import math
import Levenshtein
import tldextract

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
    """Extracts lexical features from a domain string, properly parsed."""
    # Use tldextract to correctly parse subdomain, domain, suffix
    ext = tldextract.extract(domain)
    
    # We care about the registered label and subdomain for phishing
    analysis_string = f"{ext.subdomain}{ext.domain}"
    if not analysis_string:
        analysis_string = domain
        
    length = len(domain)
    entropy = calculate_entropy(analysis_string)
    
    digit_count = sum(c.isdigit() for c in analysis_string)
    digit_ratio = digit_count / len(analysis_string) if len(analysis_string) > 0 else 0
    
    hyphen_count = analysis_string.count('-')
    
    keyword_match = any(brand in analysis_string.lower() for brand in KNOWN_BRANDS)
    
    # Calculate min Levenshtein distance to known brands
    lev_min = min((Levenshtein.distance(analysis_string.lower(), brand) for brand in KNOWN_BRANDS), default=0)

    return {
        "length": length,
        "entropy": round(entropy, 3),
        "digit_ratio": round(digit_ratio, 3),
        "hyphen_count": hyphen_count,
        "keyword_match": keyword_match,
        "levenshtein_min": lev_min
    }
