import requests
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_system():
    print("1. Authenticating as admin...")
    auth_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if auth_response.status_code != 200:
        print("Failed to authenticate!", auth_response.text)
        sys.exit(1)
        
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   -> Successfully authenticated!")

    print("\n2. Submitting domains for analysis...")
    domains = ["google.com", "g00gle.com", "example.org", "totally-legit-bank-login-secure.net"]
    
    for d in domains:
        submit_res = requests.post(
            f"{BASE_URL}/domains/analyze",
            json={"domain_name": d},
            headers=headers
        )
        if submit_res.status_code != 200:
            print(f"Failed to submit {d}!", submit_res.text)
        else:
            print(f"   -> Submitted {d}")
        
    print("\n3. Waiting for Celery background jobs to finish (5 seconds)...")
    time.sleep(5)
    
    print("\n4. Fetching analysis results...")
    list_res = requests.get(f"{BASE_URL}/domains", headers=headers, params={"limit": 10})
    
    if list_res.status_code != 200:
        print("Failed to fetch domains!", list_res.text)
        sys.exit(1)
        
    results = list_res.json()
    
    for r in results:
        print(f"\n======================================")
        print(f"Domain: {r.get('domain_name')}")
        print(f"Status: {r.get('status')}")
        if r.get('score'):
            score = r['score']['final_risk_score']
            print(f"Final Risk Score: {score:.2f}")
            if score > 0.6:
                print("⚠️  PHISHING ALERT")
            else:
                print("✅  SAFE")
        else:
            print("Score: Pending...")

if __name__ == "__main__":
    test_system()
