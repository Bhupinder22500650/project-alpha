import os
import joblib
import pandas as pd
from .feature_extractor import extract_lexical_features

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models', 'phishing_model.pkl')

model = None

def load_model():
    global model
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)

def score_domain(domain: str) -> dict:
    """
    Extracts features, runs the model, and returns a risk score (0-100)
    along with feature importance explanations.
    """
    global model
    if model is None:
        load_model()
        
    features = extract_lexical_features(domain)
    
    if model is None:
        # Fallback heuristic if model isn't trained yet
        risk = 0.0
        if features['keyword_match']: risk += 40
        if features['entropy'] > 3.5: risk += 20
        if features['digit_ratio'] > 0.1: risk += 20
        if features['levenshtein_min'] <= 2: risk += 20
        
        return {
            "risk_score": min(100.0, risk),
            "top_factors": {"heuristic": "Model not loaded, using fallback"},
            "features": features
        }

    # Run ML Model
    df = pd.DataFrame([features])
    # predict_proba returns [[prob_0, prob_1]]
    prob_phish = model.predict_proba(df)[0][1]
    risk_score = round(prob_phish * 100, 2)
    
    # Calculate simple feature importance for this prediction (naive explainability for MVP)
    # True SHAP takes more setup, this is a proxy using global feature importances scaled by actual values
    feature_names = df.columns
    importances = model.feature_importances_
    
    factors = []
    for name, imp in zip(feature_names, importances):
        if features[name] > 0: # Only highlight features that are present
            factors.append((name, imp * features[name]))
            
    factors.sort(key=lambda x: x[1], reverse=True)
    top_factors = {k: round(v, 4) for k, v in factors[:3]}
    
    return {
        "risk_score": risk_score,
        "top_factors": top_factors,
        "features": features
    }
