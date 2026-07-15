import os
import sys
import pandas as pd
import numpy as np
import random
from sklearn.linear_model import LogisticRegression
import lightgbm as lgb
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import classification_report
import joblib
import tldextract

# Add parent dir to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.feature_extractor import extract_lexical_features

def generate_realistic_synthetic_data(n=3000):
    """
    Simulates a realistic dataset using Tranco (legit) and targeted phishing generations.
    Ensures groups (campaigns) exist to test grouped splitting.
    """
    legit_domains = [
        "google.com", "apple.com", "microsoft.com", "netflix.com", 
        "amazon.com", "github.com", "wikipedia.org", "yahoo.com",
        "chase.com", "bankofamerica.com", "paypal.com", "wellsfargo.com"
    ]
    
    data = []
    
    # 1. Legit Domains
    for _ in range(n // 2):
        base = np.random.choice(legit_domains)
        prefix = np.random.choice(["", "www.", "app.", "mail.", "secure.", "login."])
        domain = f"{prefix}{base}"
        
        # Simulate enrichment features for legit
        data.append({
            "domain": domain, 
            "label": 0,
            "group": base, # Group by base domain
            "dns_a_record_count": random.randint(1, 4),
            "dns_mx_record_present": 1,
            "dns_ns_record_count": random.randint(2, 4),
            "cert_validity_days": random.randint(90, 397),
            "rdap_domain_age_days": random.randint(1000, 5000)
        })
        
    # 2. Phishing Domains
    phish_tactics = ["typo", "homoglyph", "prefix", "suffix"]
    for _ in range(n // 2):
        target = np.random.choice(legit_domains)
        ext = tldextract.extract(target)
        tactic = np.random.choice(phish_tactics)
        
        if tactic == "typo":
            phish_base = ext.domain.replace('o', '0').replace('l', '1').replace('i', 'l')
            domain = f"{phish_base}.{ext.suffix}"
        elif tactic == "homoglyph":
            domain = f"{ext.domain}-security-check.xyz"
        elif tactic == "prefix":
            domain = f"login-{ext.domain}.com"
        else:
            domain = f"{ext.domain}-billing.net"
            
        # Group by the targeted brand to ensure we don't leak campaigns
        group = target 
        
        # Simulate enrichment features for phishing
        data.append({
            "domain": domain, 
            "label": 1,
            "group": group,
            "dns_a_record_count": random.randint(1, 2),
            "dns_mx_record_present": random.choice([0, 1]),
            "dns_ns_record_count": 2,
            "cert_validity_days": random.choice([0, 90]), # often Let's Encrypt or none
            "rdap_domain_age_days": random.randint(1, 30) # recently registered
        })
        
    return pd.DataFrame(data)

def train():
    print("Generating realistic synthetic dataset...")
    df = generate_realistic_synthetic_data(4000)
    
    print("Extracting lexical features...")
    lexical_features = []
    for domain in df['domain']:
        feats = extract_lexical_features(domain)
        lexical_features.append(feats)
        
    lex_df = pd.DataFrame(lexical_features)
    
    # Combine lexical and enriched features
    full_df = pd.concat([lex_df, df[['dns_a_record_count', 'dns_mx_record_present', 'dns_ns_record_count', 'cert_validity_days', 'rdap_domain_age_days']]], axis=1)
    
    y = df['label']
    groups = df['group']
    
    # GroupShuffleSplit prevents data leakage (same base brand in train and test)
    # This is better than a random split.
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(full_df, y, groups))
    
    # --- MODEL A: Fast Lexical Model ---
    print("\n--- Training Model A (Lexical) ---")
    X_lex = lex_df
    X_train_lex, X_test_lex = X_lex.iloc[train_idx], X_lex.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    model_a = LogisticRegression(max_iter=1000)
    model_a.fit(X_train_lex, y_train)
    
    print("Evaluating Model A:")
    y_pred_a = model_a.predict(X_test_lex)
    print(classification_report(y_test, y_pred_a))
    
    # --- MODEL B: Enriched Model ---
    print("\n--- Training Model B (Enriched) ---")
    X_train_full, X_test_full = full_df.iloc[train_idx], full_df.iloc[test_idx]
    
    model_b = lgb.LGBMClassifier(n_estimators=100, random_state=42)
    model_b.fit(X_train_full, y_train)
    
    print("Evaluating Model B:")
    y_pred_b = model_b.predict(X_test_full)
    print(classification_report(y_test, y_pred_b))
    
    # Save models
    os.makedirs('models', exist_ok=True)
    joblib.dump(model_a, 'models/lexical_model.pkl')
    joblib.dump(model_b, 'models/enriched_model.pkl')
    print("Models saved successfully.")

if __name__ == "__main__":
    train()
