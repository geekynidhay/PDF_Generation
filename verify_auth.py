import requests
import json

FIREBASE_API_KEY = "AIzaSyBbkJvCQCMV9I8VrN-DxBEB8kkQ4USiIlk"
FIREBASE_DATABASE_URL = "https://pdf-maker-9de2c-default-rtdb.europe-west1.firebasedatabase.app"

def test_anon_auth():
    print(f"Testing Anonymous Auth with API Key: {FIREBASE_API_KEY[:10]}...")
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    try:
        resp = requests.post(url, json={"returnSecureToken": True}, timeout=10)
        if resp.status_code == 200:
            print("[SUCCESS] Anonymous Auth successful!")
            token = resp.json().get('idToken')
            print(f"Token received ({len(token)} chars)")
            return token
        else:
            print(f"[FAILED] Auth failed. Code: {resp.status_code}")
            print(f"Response: {resp.text}")
            return None
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return None

def test_db_read(token):
    print(f"\nTesting Database Read from {FIREBASE_DATABASE_URL}...")
    url = f"{FIREBASE_DATABASE_URL}/activation_keys.json?shallow=true"
    if token:
        url += f"&auth={token}"
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
             print("[SUCCESS] Database connection successful!")
             print(f"Data: {resp.text}")
        elif resp.status_code == 401:
             print("[FAILED] 401 Unauthorized - Token may not have permission or Rules reject Anonymous users.")
        else:
             print(f"[FAILED] Database error. Code: {resp.status_code}")
             print(resp.text)
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")

if __name__ == "__main__":
    token = test_anon_auth()
    test_db_read(token)
