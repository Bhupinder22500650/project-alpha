import os
import sys
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# Add parent dir to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.feature_extractor import extract_lexical_features

def generate_synthetic_data(n=1000):
    """
    Generates a synthetic dataset of domains for prototype training.
    Real implementation would load PhishTank / Tranco datasets.
    """
    legit_domains = [
        "google.com", "apple.com", "microsoft.com", "netflix.com", 
        "amazon.com", "github.com", "wikipedia.org", "yahoo.com"
    ]
    phish_domains = [
        "g00gle-login.com", "apple-support-verify.com", "micros0ft-update.net",
        "netf1ix-billing.com", "amaz0n-security.com", "paypa1-secure.com",
        "secure-login-attempt.com", "update-your-account-now.com"
    ]
    
    data = []
    # Generate variations
    for _ in range(n // 2):
        # Legit
        base = np.random.choice(legit_domains)
        prefix = np.random.choice(["", "www.", "app.", "mail."])
        data.append({"domain": f"{prefix}{base}", "label": 0})
        
        # Phish
        base = np.random.choice(phish_domains)
        prefix = np.random.choice(["", "secure-", "login-", "verify-"])
        data.append({"domain": f"{prefix}{base}", "label": 1})
        
    return pd.DataFrame(data)

def train():
    print("Generating synthetic dataset...")
    df = generate_synthetic_data(2000)
    
    print("Extracting features...")
    feature_list = []
    for domain in df['domain']:
        feats = extract_lexical_features(domain)
        feature_list.append(feats)
        
    X = pd.DataFrame(feature_list)
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    print("Evaluating...")
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred))
    
    # Save model
    os.makedirs('models', exist_ok=True)
    model_path = 'models/phishing_model.pkl'
    joblib.dump(clf, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train()
