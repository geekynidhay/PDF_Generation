
# -*- coding: utf-8 -*-
"""
Test script to verify Firebase activation connectivity (REST API)
"""
import requests
import json
import sys
import hashlib
import platform

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from firebase_config import FIREBASE_DATABASE_URL
except ImportError:
    FIREBASE_DATABASE_URL = "https://pdf-maker-9de2c-default-rtdb.europe-west1.firebasedatabase.app"

def test_firebase_connection():
    """Test if we can reach Firebase"""
    print(f"\n1. Testing connection to: {FIREBASE_DATABASE_URL}...")
    try:
        # Just try to read the keys path (might return null or empty dict, or 401 if secure)
        # We use .json to access the REST API
        url = f"{FIREBASE_DATABASE_URL}/activation_keys.json?shallow=true"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print(f"   [OK] Connection successful: {response.status_code}")
            print(f"   Data found: {response.text}")
            return True
        elif response.status_code == 401:
            print(f"   [OK] Connection successful (Protected): {response.status_code}")
            return True
        else:
            print(f"   [FAIL] Connection error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   [FAIL] Connection failed: {e}")
        return False

def machine_fingerprint():
    """Generate unique machine fingerprint from hardware info (Same as client app)"""
    import uuid
    import subprocess
    
    # Collect system information
    info_parts = [
        platform.node(),           # Hostname
        platform.machine(),        # Machine type
        platform.system(),         # OS name
        platform.processor(),      # Processor info
    ]
    
    # Try to get MAC address
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                       for elements in range(0, 2*6, 2)][::-1])
        info_parts.append(mac)
    except:
        pass
    
    # Try to get CPU serial or other hardware ID on Windows
    try:
        if platform.system() == 'Windows':
            result = subprocess.check_output(
                ['wmic', 'cpu', 'get', 'ProcessorId'],
                stderr=subprocess.DEVNULL
            ).decode().strip().split('\n')
            if len(result) > 1:
                info_parts.append(result[1].strip())
    except:
        pass
    
    # Combine and hash
    combined = '|'.join(filter(None, info_parts))
    return hashlib.sha256(combined.encode()).hexdigest()

def main():
    print("="*60)
    print("FP PDF Firebase Activation - Test Suite")
    print("="*60)
    
    # Run tests
    if not test_firebase_connection():
        print("\n[ERROR] Could not connect to Firebase.")
        print("Please check your FIREBASE_DATABASE_URL in firebase_config.py")
        return
    
    print(f"\nYour Machine Fingerprint: {machine_fingerprint()}")
    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Get your serviceAccountKey.json (if you are the admin)")
    print("2. Run 'admin_app.py' to generate keys")
    print("3. Run 'client_app.py' to activate")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
