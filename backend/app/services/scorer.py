import os
import joblib
import pandas as pd
from .feature_extractor import extract_lexical_features
import shap

MODEL_A_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models', 'lexical_model.pkl')
MODEL_B_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models', 'enriched_model.pkl')

model_a = None
model_b = None
explainer_b = None

def load_models():
    global model_a, model_b, explainer_b
    if os.path.exists(MODEL_A_PATH):
        model_a = joblib.load(MODEL_A_PATH)
    if os.path.exists(MODEL_B_PATH):
        model_b = joblib.load(MODEL_B_PATH)
        try:
            explainer_b = shap.TreeExplainer(model_b)
        except Exception:
            pass # fallback if not tree based

def calculate_fast_score(features: dict) -> float:
    """Calculates Model A (Fast Lexical Score)"""
    global model_a
    if model_a is None:
        load_models()
        
    if model_a is None:
        # Fallback Heuristic
        risk = 0.0
        if features['keyword_match']: risk += 40
        if features['entropy'] > 3.5: risk += 20
        if features['digit_ratio'] > 0.1: risk += 20
        if features['levenshtein_min'] <= 2: risk += 20
        return min(100.0, risk)
        
    df = pd.DataFrame([features])
    prob_phish = model_a.predict_proba(df)[0][1]
    return round(prob_phish * 100, 2)

def calculate_enriched_score(domain_obj, enrichment_obj) -> dict:
    """Calculates Model B (Enriched Score) and extracts true SHAP explanations."""
    global model_b, explainer_b
    if model_b is None:
        load_models()
        
    # Combine lexical and enrichment features
    features = {
        "length": domain_obj.features.length,
        "entropy": domain_obj.features.entropy,
        "digit_ratio": domain_obj.features.digit_ratio,
        "hyphen_count": domain_obj.features.hyphen_count,
        "keyword_match": int(domain_obj.features.keyword_match),
        "levenshtein_min": domain_obj.features.levenshtein_min,
        "dns_a_record_count": enrichment_obj.dns_a_record_count,
        "dns_mx_record_present": int(enrichment_obj.dns_mx_record_present),
        "dns_ns_record_count": enrichment_obj.dns_ns_record_count,
        "cert_validity_days": enrichment_obj.cert_validity_days or 0,
        "rdap_domain_age_days": enrichment_obj.rdap_domain_age_days or 0,
    }
    
    if model_b is None:
        # Fallback if no Model B
        base_score = calculate_fast_score(features)
        # simplistic penalty for young domains
        if features['rdap_domain_age_days'] < 30:
            base_score += 20
        # missing MX
        if not features['dns_mx_record_present']:
            base_score += 10
            
        return {
            "risk_score": min(100.0, base_score),
            "top_factors": {"fallback": "Model B not loaded."}
        }
        
    df = pd.DataFrame([features])
    prob_phish = model_b.predict_proba(df)[0][1]
    risk_score = round(prob_phish * 100, 2)
    
    top_factors = {}
    if explainer_b:
        # True SHAP Values
        shap_values = explainer_b.shap_values(df)
        
        # Binary classification usually returns a list of arrays or array of shape (n, features, classes)
        # Handle depending on shap/model version
        if isinstance(shap_values, list):
            sv = shap_values[1][0] # class 1
        elif len(shap_values.shape) == 3:
            sv = shap_values[0, :, 1]
        else:
            sv = shap_values[0]
            
        factors = list(zip(df.columns, sv))
        factors.sort(key=lambda x: abs(x[1]), reverse=True)
        top_factors = {k: round(v, 4) for k, v in factors[:5]}
    else:
        # Fallback feature importances
        if hasattr(model_b, 'feature_importances_'):
            factors = list(zip(df.columns, model_b.feature_importances_))
            factors.sort(key=lambda x: x[1], reverse=True)
            top_factors = {k: round(float(v), 4) for k, v in factors[:5]}
            
    return {
        "risk_score": risk_score,
        "top_factors": top_factors
    }
